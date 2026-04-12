import io
import datetime
from flask import Blueprint, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from db import get_db
from middleware.auth import require_auth

reports_bp = Blueprint("reports", __name__)

PRIMARY    = colors.HexColor("#2d5016")
ACCENT     = colors.HexColor("#C8891A")
PARCHMENT  = colors.HexColor("#F5F0E8")
LIGHT_GREY = colors.HexColor("#f0f0f0")
NAVY       = colors.HexColor("#1e3a8a")

REGIONS = ["NORD", "SUD", "EST", "OUEST", "CENTRE"]


def _ndvi_interpretation(ndvi_jan_may_mean, ndvi_may, region):
    if ndvi_jan_may_mean is None:
        return "Insufficient NDVI data to generate a recommendation."
    if ndvi_jan_may_mean >= 0.55:
        return (f"{region} shows strong pre-harvest vegetation (growth-phase NDVI mean {ndvi_jan_may_mean:.3f}, "
                f"peak May NDVI {ndvi_may:.3f}). Above-average cane biomass expected — plan for higher mill throughput.")
    elif ndvi_jan_may_mean >= 0.45:
        return (f"{region} shows moderate pre-harvest vegetation (growth-phase NDVI mean {ndvi_jan_may_mean:.3f}, "
                f"peak May NDVI {ndvi_may:.3f}). Yield expected near the historical average.")
    else:
        return (f"{region} shows below-average pre-harvest vegetation (growth-phase NDVI mean {ndvi_jan_may_mean:.3f}, "
                f"peak May NDVI {ndvi_may:.3f}). Monitor closely — lower-than-average yield may require resource reallocation.")


@reports_bp.route("/reports/generate", methods=["POST"])
@require_auth
def generate_report():
    data   = request.get_json()
    region = (data.get("region") or "").upper() if data else ""
    season = data.get("season") if data else None

    if region and region not in REGIONS:
        return jsonify({"error": f"region must be one of {REGIONS}"}), 400
    if not season:
        return jsonify({"error": "season is required"}), 400

    db     = get_db()
    season = int(season)

    regions_to_report = [region] if region else REGIONS

    # ── Active model config ──────────────────────────────────────────────────
    model_config = db.model_config.find_one({"is_active": True})

    # ── Gather per-region data ───────────────────────────────────────────────
    report_rows = []
    for r in regions_to_report:
        # Most recent prediction for this region/season by the active model
        query = {"region": r, "season": season}
        if model_config:
            query["model_used"] = model_config["type"]
        pred = db.predictions.find_one(query, sort=[("created_at", -1)])

        # Harvest actuals
        harvest = db.harvest_data.find_one({"region": r, "season": season}, sort=[("week", -1)])

        # NDVI: prefer feature_snapshot stored in the prediction (exact values used)
        snapshot = pred.get("feature_snapshot", {}) if pred else {}
        if not snapshot:
            feat = db.pre_harvest_features.find_one({"region": r, "season": season})
            snapshot = {
                "ndvi_jan_may_mean": feat.get("ndvi_jan_may_mean") if feat else None,
                "ndvi_may":          feat.get("ndvi_may")          if feat else None,
                "ndvi_growth":       feat.get("ndvi_growth")       if feat else None,
                "cyclone_max_wind":  feat.get("cyclone_max_wind")  if feat else None,
                "enso_oni_djf":      feat.get("enso_oni_djf")      if feat else None,
                "surface_prev":      feat.get("surface_prev")      if feat else None,
            }

        report_rows.append({
            "region":            r,
            "predicted_tch":     pred["predicted_tch"]       if pred    else None,
            "actual_tch":        harvest["tch"]               if harvest else None,
            "surface_harvested": harvest.get("surface_harvested") if harvest else None,
            "model_used":        pred["model_used"]           if pred    else "N/A",
            "created_at":        pred.get("created_at")       if pred    else None,
            "ndvi_jan_may_mean": snapshot.get("ndvi_jan_may_mean"),
            "ndvi_may":          snapshot.get("ndvi_may"),
            "ndvi_growth":       snapshot.get("ndvi_growth"),
            "cyclone_max_wind":  snapshot.get("cyclone_max_wind"),
            "enso_oni_djf":      snapshot.get("enso_oni_djf"),
            "surface_prev":      snapshot.get("surface_prev"),
        })

    pdf_buffer = _build_pdf(report_rows, season, model_config, request.user["email"])
    filename   = f"rekolte_report_{season}{'_' + region if region else ''}.pdf"
    return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)


def _build_pdf(report_rows, season, model_config, generated_by):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    title_s    = S("t",  fontSize=22, textColor=PRIMARY,       spaceAfter=4,  fontName="Helvetica-Bold")
    subtitle_s = S("st", fontSize=11, textColor=ACCENT,        spaceAfter=2)
    meta_s     = S("m",  fontSize=9,  textColor=colors.grey,   spaceAfter=10)
    h2_s       = S("h2", fontSize=13, textColor=PRIMARY,       spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
    body_s     = S("b",  fontSize=10, spaceAfter=4)
    small_s    = S("sm", fontSize=9,  textColor=colors.grey,   spaceAfter=8)
    label_s    = S("lb", fontSize=9,  textColor=colors.grey)

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Rékolte", title_s))
    story.append(Paragraph("Sugarcane Yield Prediction System — Mauritius", subtitle_s))
    story.append(Paragraph(
        f"Season {season} Report  ·  Generated {datetime.datetime.utcnow().strftime('%d %B %Y at %H:%M')} UTC  ·  {generated_by}",
        meta_s,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.4*cm))

    # ── Model information ────────────────────────────────────────────────────
    if model_config:
        story.append(Paragraph("Active Model", h2_s))

        model_type = model_config.get("type", "N/A")
        loso_r2    = model_config.get("loso_r2",   0) or 0
        loso_rmse  = model_config.get("loso_rmse", 0) or 0
        loso_mae   = model_config.get("loso_mae",  0) or 0
        test_r2    = model_config.get("test_r2",   0) or 0
        test_rmse  = model_config.get("test_rmse", 0) or 0
        test_mae   = model_config.get("test_mae",  0) or 0
        filepath   = model_config.get("filepath",  "—")

        model_data = [
            ["", "R²", "RMSE (TCH)", "MAE (TCH)"],
            ["LOSO Cross-Validation",   f"{loso_r2:.4f}", f"{loso_rmse:.2f}", f"{loso_mae:.2f}"],
            ["2025 Holdout",            f"{test_r2:.4f}", f"{test_rmse:.2f}", f"{test_mae:.2f}"],
        ]
        col_w = [6*cm, 3*cm, 3*cm, 3*cm]
        mt = Table(model_data, colWidths=col_w)
        mt.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, LIGHT_GREY]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
            ("FONTNAME",    (0, 1), (0, -1),  "Helvetica-Bold"),
        ]))
        story.append(Paragraph(f"<b>Model:</b> {model_type}  ·  <b>File:</b> {filepath}", body_s))
        story.append(mt)
        story.append(Spacer(1, 0.3*cm))

        # Top feature importances
        fi = model_config.get("feature_importance", [])
        if fi:
            top = sorted(fi, key=lambda x: x.get("importance", 0), reverse=True)[:8]
            story.append(Paragraph("Top Predictive Features", h2_s))
            fi_data = [["Feature", "Importance"]]
            for f in top:
                fi_data.append([f["feature"], f"{f['importance']:.4f}"])
            fi_table = Table(fi_data, colWidths=[10*cm, 5*cm])
            fi_table.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
                ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, LIGHT_GREY]),
                ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
            ]))
            story.append(fi_table)
            story.append(Spacer(1, 0.3*cm))

    # ── Yield predictions table ──────────────────────────────────────────────
    story.append(Paragraph("Yield Predictions by Region", h2_s))

    pred_data = [["Region", "Predicted TCH", "Actual TCH", "Difference", "Surface (ha)"]]
    total_predicted_prod = 0
    for row in report_rows:
        pred   = row["predicted_tch"]
        actual = row["actual_tch"]
        surf   = row["surface_harvested"]
        diff   = f"{pred - actual:+.2f}" if pred is not None and actual is not None else "—"

        if pred is not None and surf is not None:
            total_predicted_prod += pred * surf

        pred_data.append([
            row["region"],
            f"{pred:.2f}"  if pred   is not None else "—",
            f"{actual:.2f}" if actual is not None else "Pending",
            diff,
            f"{surf:,.0f}" if surf is not None else "—",
        ])

    pt = Table(pred_data, colWidths=[3*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    pt.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, LIGHT_GREY]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(pt)

    if total_predicted_prod > 0:
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f"<b>Estimated national cane production:</b> {total_predicted_prod:,.0f} tonnes "
            f"(sum of predicted TCH × harvested surface per region)",
            small_s,
        ))
    story.append(Spacer(1, 0.4*cm))

    # ── Satellite features & recommendations ────────────────────────────────
    story.append(Paragraph("Pre-Harvest Satellite Features & Recommendations", h2_s))
    story.append(Paragraph(
        "Features derived from MODIS MOD13Q1 NDVI (Oct–May), CHIRPS rainfall and ERA5 temperature. "
        "NDVI Growth = ndvi_may − ndvi_oct (net vegetative gain over the pre-harvest window).",
        small_s,
    ))

    feat_data = [["Region", "NDVI Growth Phase Mean", "Peak NDVI (May)", "NDVI Growth", "Cyclone Wind", "ENSO ONI"]]
    for row in report_rows:
        feat_data.append([
            row["region"],
            f"{row['ndvi_jan_may_mean']:.3f}" if row["ndvi_jan_may_mean"] is not None else "—",
            f"{row['ndvi_may']:.3f}"           if row["ndvi_may"]          is not None else "—",
            f"{row['ndvi_growth']:.3f}"        if row["ndvi_growth"]       is not None else "—",
            f"{row['cyclone_max_wind']:.1f} km/h" if row["cyclone_max_wind"] is not None else "—",
            f"{row['enso_oni_djf']:.2f}"       if row["enso_oni_djf"]      is not None else "—",
        ])

    ft = Table(feat_data, colWidths=[2.5*cm, 4*cm, 3.5*cm, 3*cm, 3*cm, 2*cm])
    ft.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, LIGHT_GREY]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(ft)
    story.append(Spacer(1, 0.4*cm))

    # ── Region-level recommendations ─────────────────────────────────────────
    story.append(Paragraph("Agronomic Recommendations", h2_s))
    for row in report_rows:
        story.append(Paragraph(f"<b>{row['region']}</b>", body_s))
        story.append(Paragraph(
            _ndvi_interpretation(row["ndvi_jan_may_mean"], row["ndvi_may"], row["region"]),
            small_s,
        ))

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Generated by Rékolte — Sugarcane Yield Prediction System  ·  "
        "Middlesex University Mauritius  ·  M01006629",
        meta_s,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
