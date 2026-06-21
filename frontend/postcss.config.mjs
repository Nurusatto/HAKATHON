const config = {
  plugins: {
    "@tailwindcss/postcss": {},
    "postcss-pxtorem": {
      rootValue: 16,
      unitPrecision: 5,
      propList: ["*", "!letter-spacing"],
      selectorBlackList: [],
      replace: true,
      mediaQuery: true,
      minPixelValue: 4,
      exclude: /node_modules/i,
    },
  },
};

export default config;
