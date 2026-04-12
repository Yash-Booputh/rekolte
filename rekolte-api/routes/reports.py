import io
import datetime
from flask import Blueprint, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from db import get_db
from middleware.auth import require_auth

reports_bp = Blueprint("reports", __name__)

PRIMARY = colors.HexColor("#2d5016")
ACCENT = colors.HexColor("#C8891A")
PARCHMENT = colors.HexColor("#F5F0E8")
LIGHT_GREY = colors.HexColor("#f0f0f0")

REGIONS = ["NORD", "SUD", "EST", "OUEST", "CENTRE"]

def _ndvi_interpretation(ndvi_mean, region, season):
    """Return a plain-English recommendation based on NDVI vs historical context."""
    if ndvi_mean is None:
        return "Insufficient NDVI data to generate a recommendation."
    if ndvi_mean >= 0.55:
        return (f"{region} shows strong vegetation health (NDVI {ndvi_mean:.3f}). "
                "Above-average cane biomass expected — plan for higher throughput at the mill.")
    elif ndvi_mean >= 0.45:
        return (f"{region} shows moderate vegetation health (NDVI {ndvi_mean:.3f}). "
                "Yield expected near the historical average.")
    else:
        return (f"{region} shows below-average vegetation health (NDVI {ndvi_mean:.3f}). "
                "Monitor closely — lower-than-average yield may require resource reallocation.")

@reports_bp.route("/reports/generate", methods=["POST"])
@require_auth
def generate_report():
    data = request.get_json()
    region = (data.get("region") or "").upper() if data else ""
    season = data.get("season") if data else None

    if region and region not in REGIONS:
        return jsonify({"error": f"region must be one of {REGIONS}"}), 400
    if not season:
        return jsonify({"error": "season is required"}), 400

    db = get_db()
    season = int(season)

    # Gather data
    regions_to_report = [region] if region else REGIONS

    report_data = []
    for r in regions_to_report:
        pred = db.predictions.find_one({"region": r, "season": season}, sort=[("created_at", -1)])
        feat = db.pre_harvest_features.find_one({"region": r, "season": season})
        harvest = db.harvest_data.find_one({"region": r, "season": season}, sort=[("week", -1)])

        report_data.append({
            "region": r,
            "predicted_tch": pred["predicted_tch"] if pred else None,
            "actual_tch": harvest["tch"] if harvest else None,
            "model_used": pred["model_used"] if pred else "N/A",
            "ndvi_mean": feat["ndvi_jan_may_mean"] if feat else None,
            "ndvi_max":  feat["ndvi_may"]          if feat else None,
            "surface_harvested": harvest.get("surface_harvested") if harvest else None,
        })

    # Active model metrics
    model_config = db.model_config.find_one({"is_active": True})

    pdf_buffer = _build_pdf(report_data, season, model_config)

    filename = f"rekolte_report_{season}{'_' + region if region else ''}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

def _build_pdf(report_data, season, model_config):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"],
                                 textColor=PRIMARY, fontSize=20, spaceAfter=4)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"],
                                    textColor=ACCENT, fontSize=11, spaceAfter=2)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"],
                                   textColor=PRIMARY, fontSize=13, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, spaceAfter=4)
    italic_style = ParagraphStyle("italic", parent=styles["Normal"], fontSize=9,
                                  textColor=colors.grey, spaceAfter=10)

    story = []

    # Header
    story.append(Paragraph("Rékolte", title_style))
    story.append(Paragraph("Sugarcane Yield Prediction System — Mauritius", subtitle_style))
    story.append(Paragraph(
        f"Season Report: {season} | Generated: {datetime.datetime.utcnow().strftime('%d %B %Y, %H:%M')} UTC",
        italic_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.4*cm))

    # Model info
    if model_config:
        story.append(Paragraph("Model Information", heading_style))
        model_table_data = [
            ["Model Type", "R²", "RMSE", "MAE"],
            [
                model_config.get("type", "N/A"),
                f"{model_config.get('r_squared', 0):.3f}",
                f"{model_config.get('rmse', 0):.2f}",
                f"{model_config.get('mae', 0):.2f}",
            ]
        ]
        model_table = Table(model_table_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
        model_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (-1, -1), PARCHMENT),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, LIGHT_GREY]),
        ]))
        story.append(model_table)
        story.append(Spacer(1, 0.5*cm))

    # Predictions table
    story.append(Paragraph("Yield Predictions by Region", heading_style))
    pred_table_data = [["Region", "Predicted TCH", "Actual TCH", "Difference", "Surface (ha)"]]
    for row in report_data:
        pred = row["predicted_tch"]
        actual = row["actual_tch"]
        diff = f"{pred - actual:+.2f}" if pred is not None and actual is not None else "—"
        pred_table_data.append([
            row["region"],
            f"{pred:.2f}" if pred is not None else "—",
            f"{actual:.2f}" if actual is not None else "Pending",
            diff,
            f"{row['surface_harvested']:,.0f}" if row.get("surface_harvested") else "—",
        ])

    pred_table = Table(pred_table_data, colWidths=[3*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    pred_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 0.5*cm))

    # NDVI summary + recommendations
    story.append(Paragraph("NDVI Analysis & Recommendations", heading_style))
    for row in report_data:
        story.append(Paragraph(f"<b>{row['region']}</b>", body_style))
        ndvi_text = (f"NDVI Mean: {row['ndvi_mean']:.3f} | NDVI Max: {row['ndvi_max']:.3f}"
                     if row["ndvi_mean"] is not None else "No NDVI data available.")
        story.append(Paragraph(ndvi_text, italic_style))
        story.append(Paragraph(
            _ndvi_interpretation(row["ndvi_mean"], row["region"], season),
            body_style,
        ))
        story.append(Spacer(1, 0.2*cm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Generated by Rékolte — Sugarcane Yield Prediction System | Middlesex University Mauritius",
        italic_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
