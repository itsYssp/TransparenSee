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
    },
  },
  plugins: [],
};
