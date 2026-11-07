import { registerRootComponent } from 'expo';

import App from './src/App';

// Entry point switched from expo-router/entry (TEST-AUDIT Critical-2):
// the package.json declared expo-router as the entry but the project has
// no app/ routes directory and src/App.tsx uses @react-navigation
// directly, so booting previously rendered nothing. registerRootComponent
// also keeps this working in Expo Go and in bare prebuilds.
// If the app migrates to expo-router later, create app/ routes and point
// "main" back at expo-router/entry.
registerRootComponent(App);
