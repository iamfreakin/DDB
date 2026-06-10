export type Mood =
  | "warm"
  | "friendly"
  | "emotional"
  | "premium"
  | "playful"
  | "clean"
  | "trustworthy";

export interface BrandProfile {
  id: string;
  version: number;
  products: string[];
  target_customers: string;
  strengths: string;
  desired_moods: Mood[];
  region: string | null;
  price_range: string | null;
  existing_copy: string | null;
  avoid_expressions: string[];
  campaign_facts: Record<string, string>;
  created_at: string;
}

export interface Brand {
  id: string;
  name: string;
  industry: string;
  active_profile: BrandProfile;
  created_at: string;
  updated_at: string;
}

export interface Analysis {
  id: string;
  profile_version_id: string;
  status: "draft" | "approved" | "stale" | "superseded";
  brand_summary: string;
  target_segments: string[];
  customer_needs: string[];
  value_proposition: string;
  differentiators: string[];
  brand_voice: string[];
  recommended_keywords: string[];
  avoid_expressions: string[];
  missing_information: string[];
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  brand_id: string;
  brand_analysis_id: string;
  name: string;
  goal: string;
  start_date: string;
  end_date: string;
  status: string;
  highlighted_products: string[];
  required_facts: Record<string, string>;
}

export interface Strategy {
  id: string;
  campaign_id: string;
  version: number;
  core_message: string;
  weekly_goals: { week: number; goal: string }[];
  content_pillars: string[];
  post_topics: {
    sequence: number;
    week: number;
    topic: string;
    content_type: string;
  }[];
  risk_notes: string[];
}

export interface Variant {
  id: string;
  content_id: string;
  origin: "ai" | "user_edit";
  variant_number: number;
  tone: string;
  opening_line: string;
  body: string;
  cta: string;
  hashtags: string[];
  image_concept: string;
}

export interface PosterBrief {
  id: string;
  content_id: string;
  headline: string;
  supporting_text: string | null;
  visual_mood: string;
  colors: string[];
  layout_description: string;
  image_prompt: string;
  negative_prompt: string | null;
  aspect_ratio: string;
}

export interface GeneratedImage {
  id: string;
  poster_brief_id: string;
  version: number;
  status: "draft" | "approved" | "superseded";
  provider: string;
  model: string;
  prompt: string;
  aspect_ratio: string;
  width: number;
  height: number;
  generation_run_id: string | null;
  approved_at: string | null;
  created_at: string;
}

export interface Content {
  id: string;
  campaign_id: string;
  sequence: number;
  week_number: number;
  content_type: string;
  topic: string;
  core_message: string;
  status: string;
  selected_variant_id: string | null;
  variants: Variant[];
  poster_brief: PosterBrief | null;
}

export interface CalendarItem {
  id: string;
  campaign_id: string;
  content_id: string;
  scheduled_date: string;
  status: string;
  content: Content | null;
  approved_image: GeneratedImage | null;
}
