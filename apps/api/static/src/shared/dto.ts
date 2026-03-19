export type PaginationResponse<T> = {
  items: T[];
  next_cursor: string | null;
  prev_cursor: string | null;
};

export type SpaceRead = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  created_by_user_id: string;
};

export type ChannelRead = {
  id: string;
  space_id: string | null;
  type: "direct" | "group" | "topic";
  name: string | null;
  is_private: boolean;
  created_at: string;
  created_by_user_id: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterRequest = {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  display_name: string;
  password: string;
};

export type UserBrief = {
  id: string;
  display_name: string;
  avatar_url: string | null;
};

export type MessageContent = {
  type:
    | "text/plain"
    | "code/block"
    | "mock/image"
    | "git/reference"
    | "custom_tool_response";
  data: Record<string, unknown>;
  order: number;
};

export type MessageRead = {
  id: string;
  channel_id: string;
  thread_id: string | null;
  parent_message_id: string | null;
  sender: UserBrief;
  status: "sent" | "delivered" | "read" | "failed";
  sent_at: string;
  edited_at: string | null;
  contents: MessageContent[];
};

export type SpaceCreate = {
  name: string;
  description: string | null;
};

export type ChannelCreate = {
  space_id: string | null;
  type: "direct" | "group" | "topic";
  name: string | null;
  is_private: boolean;
  member_ids: string[] | null;
};

export type MessageCreate = {
  thread_id: string | null;
  parent_message_id: string | null;
  contents: Array<{
    type: MessageContent["type"];
    data: Record<string, unknown>;
    order: number;
  }>;
};

