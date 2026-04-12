import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'mu.ac.mua.rekolte',
  appName: 'Rékolte',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
  plugins: {
    GoogleAuth: {
      // Android OAuth client ID (Web client ID works for token verification)
      // Replace with your actual Web Client ID from Google Cloud Console
      clientId: process.env.VITE_GOOGLE_CLIENT_ID ?? '',
      scopes: ['profile', 'email'],
      grantOfflineAccess: false,
    },
  },
};

export default config;
