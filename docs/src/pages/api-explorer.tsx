import React from "react";
import Layout from "@theme/Layout";
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";

const SPEC_URL = "/sentinel-sdk/openapi.json";

export default function ApiExplorer(): JSX.Element {
  return (
    <Layout title="API Explorer" description="Interactive OpenAPI reference for the Kallon Platform API">
      <main style={{ maxWidth: "100%", margin: "0 auto", padding: "1rem 0 3rem" }}>
        <div style={{ padding: "0 1.5rem 1rem" }}>
          <h1>API Explorer</h1>
          <p>
            Full Platform API — fleet, tower proxy, alerts, and enrollment. Served live at{" "}
            <code>GET /openapi.json</code> on your control plane; this page bundles the spec
            from the <code>sentinel-customer</code> branch.
          </p>
        </div>
        <SwaggerUI url={SPEC_URL} docExpansion="list" defaultModelsExpandDepth={0} />
      </main>
    </Layout>
  );
}
