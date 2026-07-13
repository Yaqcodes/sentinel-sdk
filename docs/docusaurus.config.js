// @ts-check
const { themes } = require("prism-react-renderer");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Sentinel SDK",
  tagline: "Developer reference for the Kallon Sentry Tower platform",
  url: "https://yaqcodes.github.io",
  baseUrl: "/sentinel-sdk/",
  organizationName: "Yaqcodes",
  projectName: "sentinel-sdk",
  onBrokenLinks: "warn",
  onBrokenMarkdownLinks: "warn",
  i18n: { defaultLocale: "en", locales: ["en"] },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: "/", // docs-only site
          sidebarPath: require.resolve("./sidebars.js"),
          editUrl: "https://github.com/Yaqcodes/sentinel-sdk/tree/main/docs/",
        },
        blog: false,
        theme: { customCss: require.resolve("./src/css/custom.css") },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: "Sentinel SDK",
        items: [
          { type: "docSidebar", sidebarId: "docs", position: "left", label: "Documentation" },
          { to: "/api-explorer", label: "API Explorer", position: "left" },
          { href: "https://github.com/Yaqcodes/sentinel-sdk", label: "GitHub", position: "right" },
        ],
      },
      footer: {
        style: "dark",
        copyright: `Terra Industries · Kallon Sentry Tower Platform`,
      },
      prism: {
        theme: themes.github,
        darkTheme: themes.dracula,
        additionalLanguages: ["bash", "json", "python"],
      },
    }),
};

module.exports = config;
