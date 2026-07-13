export interface Customer {
  customer_id: string;
  display_name: string;
  vpn_subnet: string;
  gateway_id?: string | null;
  gateway_endpoint?: string | null;
  gateway_public_key?: string | null;
  hub_alert_url?: string | null;
  hub_provider?: string | null;
  hub_host_id?: string | null;
  status: string;
  created_at?: string | null;
}

export interface Tower {
  device_id: string;
  customer_id: string;
  group_id?: string | null;
  vpn_ip?: string | null;
  wg_public_key?: string | null;
  status: string;
  acceptance_status?: string;
  manufactured_at?: string | null;
  enrolled_at?: string | null;
  shipped_at?: string | null;
  rtsp_base?: string | null;
}

export interface StreamPath {
  name: string;
  ready: boolean;
  readers: number;
  source: string | null;
}

export interface PlatformAlert {
  device_id: string;
  customer_id?: string | null;
  alert_type: string;
  kind?: string;
  severity: string;
  timestamp_utc?: string | null;
  nonce?: string | null;
  details?: Record<string, unknown>;
  received_utc?: string | null;
}

export interface PtzMoveBody {
  camera?: number;
  mode: 'absolute' | 'continuous';
  pan?: number;
  tilt?: number;
  zoom?: number;
  seconds?: number;
}

export interface PtzStopBody {
  camera?: number;
  home?: boolean;
}

export interface PtzStatusResult {
  ok?: boolean;
  result?: {
    pan?: number;
    tilt?: number;
    zoom?: number;
    pan_deg?: number;
    tilt_deg?: number;
    zoom_ratio?: number;
  };
}

export interface StreamsResponse {
  available: boolean;
  error?: string;
  paths: StreamPath[];
}

export type StatusResponse = Record<string, unknown> & {
  available?: boolean;
  error?: string;
  device_id?: string;
};
