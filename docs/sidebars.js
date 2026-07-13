// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    "intro",
    {
      type: "category",
      label: "API Reference",
      collapsed: false,
      items: [
        "api/overview",
        "api/customers",
        "api/towers",
        "api/ptz",
        "api/snapshot",
        "api/telemetry",
        "api/alerts-api",
        "api/enrollment",
      ],
    },
    {
      type: "category",
      label: "Guides",
      collapsed: false,
      items: [
        "guides/alerts",
        "guides/rtsp",
        "guides/tower-bring-up",
      ],
    },
  ],
};

module.exports = sidebars;
