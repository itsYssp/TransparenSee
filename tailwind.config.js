module.exports = {
  content: [
    "./app/templates/**/*.{html,js}",
    "./app/**/*.html",
    "./TransparenSee/templates/**/*.{html,js}",
    "./static/js/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        spaceGrotesk: ["Space Grotesk", "sans-serif"],
      },
      colors: {
        navy: {
          DEFAULT: "#0f2044",
          mid: "#1a3460",
          light: "#243e6e",
        },
        teal: {
          DEFAULT: "#0d9488",
          light: "#14b8a6",
          50: "#f0fdfa",
        },
        gold: "#f59e0b",
        cream: "#faf8f4",
      },
    },
  },
  plugins: [],
};
