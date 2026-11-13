export type UserRole = "driver" | "mechanic" | "manager";
export type RegistrationRole = Exclude<UserRole, "manager">;
export type MechanicService =
  | "Tire Repair"
  | "Towing Service"
  | "Battery Jumpstart"
  | "Electrical Issues"
  | "Engine Repair"
  | "Bodywork/Collision Repair"
  | "Other Repair Service"
  | "General Mechanics/All Services";

export interface MobileRegistrationInput {
  role: RegistrationRole;
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  mobile: string;
  address?: string;
  license_no?: string;
  vehicle_model?: string;
  state?: string;
  local_government?: string;
  union_name?: string;
  union_location?: string;
  services?: MechanicService[];
}

export interface MobileRegistrationResponse {
  detail: string;
  role: RegistrationRole;
  verification_required: boolean;
}

export interface MobileUser {

  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_email_verified: boolean;
  is_approved: boolean;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface LoginResponse extends TokenPair {
  user: MobileUser;
}

export interface ServiceRequest {
  id: number;
  category: string;
  vehicle_no: string | null;
  vehicle_name: string | null;
  location: string | null;
  state: string | null;
  latitude: string | number | null;
  longitude: string | number | null;
  mechanic_location: string | null;
  status: string;
  date: string;
  estimated_completion_date: string | null;
  eta: string | null;
  problem_description: string | null;
  currency: string | null;
  cost: string | number | null;
  tax: string | number | null;
}

export type MechanicRequestAction = "accept" | "start" | "complete";

export type ServiceCategory =
  | "Tire Repair"
  | "Towing Service"
  | "Battery Jumpstart"
  | "Electrical Issues"
  | "Engine Repair"
  | "Bodywork/Collision Repair"
  | "Other Service";

export interface RequestCreateInput {
  category: ServiceCategory;
  vehicle_no: string;
  vehicle_name: string;
  problem_description: string;
  state: string;
  location: string;
  mobile: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface RequestPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: ServiceRequest[];
}

export interface ManagerMechanicSummary {
  id: number;
  full_name: string;
  union_name: string | null;
  state: string;
  local_government: string;
  is_approved: boolean;
  can_be_assigned: boolean;
  assigned_request_count: number;
  active_request_count: number;
}

export interface ManagerMechanicPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: ManagerMechanicSummary[];
}

export interface ManagerQueueRequest {
  id: number;
  category: string;
  vehicle_no: string;
  vehicle_name: string;
  location: string;
  state: string;
  problem_description: string;
  status: string;
  date: string;
}

export interface ManagerQueuePage {
  count: number;
  next: string | null;
  previous: string | null;
  results: ManagerQueueRequest[];
}

export interface MobileNotification {
  id: number;
  message: string;
  timestamp: string;
  is_read: boolean;
}

export interface NotificationPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: MobileNotification[];
}
