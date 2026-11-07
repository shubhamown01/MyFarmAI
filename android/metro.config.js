const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// svg-transformer block removed (TEST-AUDIT Critical-1): the package was
// never installed and nothing in src/ uses SVG, so Metro crashed at
// startup for every bundle. The assetExt/sourceExt svg filtering above is
// harmless to keep; restore the transformer only if SVGs are introduced
// (with react-native-svg added to package.json).

module.exports = config;
