export type UserRole = "driver" | "mechanic" | "manager";

export interface TokenPair {
  access: string;
  refresh: string;
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

export interface RequestPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: ServiceRequest[];
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
