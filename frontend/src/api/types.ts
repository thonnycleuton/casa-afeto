export interface HealthResponse {
  status: string
  environment: string
  project_name: string
}

export type ProductUnit = 'UN' | 'KG' | 'G' | 'L' | 'ML'
export type CustomerStatus = 'ACTIVE' | 'INACTIVE'

export interface CustomerInput {
  name: string
  phone: string
  email?: string | null
  notes?: string | null
}

export interface Customer extends CustomerInput {
  id: number
  status: CustomerStatus
  created_at: string
  updated_at: string
  warning?: { code: string } | null
}

export interface ImportantDateInput {
  description: string
  recurring: boolean
  day?: number | null
  month?: number | null
  date?: string | null
}

export interface ImportantDate extends ImportantDateInput {
  id: number
  customer_id: number
  status: CustomerStatus
  created_at: string
  updated_at: string
}

export interface ProductInput {
  name: string
  base_unit: ProductUnit
  reference_price?: string | null
  commercial_conversion_factor?: string | null
  image_url?: string | null
}

export interface Product extends ProductInput {
  id: number
  active: boolean
  reference_price?: string | null
  commercial_conversion_factor?: string | null
  image_url?: string | null
  inventory_balance: string
  created_at: string
  updated_at: string
}

export interface InventoryMovement {
  id: number
  product_id: number
  quantity: string
  type: 'ENTRY' | 'ADJUSTMENT' | 'OUTPUT'
  unit_cost?: string | null
  sale_id?: number | null
  purchase_id?: number | null
  batch_id?: number | null
  created_at: string
}

export interface StockBatch {
  id: number
  product_id: number
  purchase_id?: number | null
  purchase_item_id?: number | null
  quantity_original: string
  quantity_remaining: string
  unit_cost?: string | null
  status: 'ACTIVE' | 'EXHAUSTED'
  expiry_date?: string | null
  expiry_status?: 'OK' | 'WARNING' | 'EXPIRED' | null
  created_at: string
}

export interface ExpiryAlert {
  batch_id: number
  product_id: number
  product_name: string
  quantity_remaining: string
  unit_cost?: string | null
  expiry_date: string
  expiry_status: 'WARNING' | 'EXPIRED'
  days_until_expiry: number
  purchase_id?: number | null
}

export interface ReplenishmentItem {
  product_id: number
  product_name: string
  stock_quantity: string
  estimated_need: string
  urgent_need: string
  total_need: string
  shortage: string
  status: 'OK' | 'BAIXO' | 'CRÍTICO'
}

export interface ReplenishmentList {
  items: ReplenishmentItem[]
  total: number
}

export interface CompositionItem {
  product_id: number
  product_name: string
  product_active: boolean
  base_unit: ProductUnit
  quantity: string
  inventory_balance: string
  stock_available: boolean
  stock_shortage: string
  unit_cost?: string | null
  total_cost?: string | null
}

export interface BasketTemplate {
  id: number
  name: string
  active: boolean
  price: string | null
  estimated_cost?: string | null
  suggested_price?: string | null
  has_reliable_cost?: boolean
  created_at: string
  updated_at: string
  items: CompositionItem[]
}

export interface CompositionInput {
  product_id: number
  quantity: string
}

export type SaleStatus =
  | 'RASCUNHO'
  | 'CONFIRMADA'
  | 'EM PREPARAÇÃO'
  | 'PRONTA'
  | 'ENTREGUE'
  | 'CANCELADA'

export interface SaleBasketItem {
  id: number
  product_id: number
  product_name: string
  product_unit: ProductUnit
  quantity: string
}

export interface SaleCompositionHistory {
  id: number
  sale_basket_id: number
  previous_items: Array<{
    product_id: number
    product_name: string
    quantity: string
    unit: string
  }>
  new_items: Array<{
    product_id: number
    product_name: string
    quantity: string
    unit: string
  }>
  operator_name: string
  created_at: string
}

export interface SaleDeliveryHistory {
  id: number
  sale_basket_id: number
  operator_name: string
  delivered_at: string
}

export interface SaleReopenHistory {
  id: number
  sale_id: number
  reason: string
  operator_name: string
  created_at: string
}

export interface SaleBasket {
  id: number
  sale_id: number
  name: string
  origin_template_id: number | null
  price: string
  recipient_name: string | null
  delivery_address: string | null
  delivery_date: string | null
  delivery_time: string | null
  is_prepared: boolean
  is_delivered: boolean
  created_at: string
  updated_at: string
  items: SaleBasketItem[]
  composition_histories: SaleCompositionHistory[]
  delivery_histories: SaleDeliveryHistory[]
}

export interface Sale {
  id: number
  customer_id: number
  customer_name: string
  customer_phone: string
  status: SaleStatus
  total: string
  created_at: string
  updated_at: string
  baskets: SaleBasket[]
  reopen_histories: SaleReopenHistory[]
}

export interface SaleBasketAddInput {
  template_id: number
  recipient_name?: string | null
  delivery_address?: string | null
  delivery_date?: string | null
  delivery_time?: string | null
  price?: string | null
}

export interface SaleCreateInput {
  customer_id: number
  baskets: SaleBasketAddInput[]
}

// --- M6: Purchases ---

export interface PurchaseItemInput {
  product_id: number
  commercial_unit?: string | null
  conversion_factor: string
  commercial_quantity: string
  commercial_unit_price: string
  expiry_date?: string | null
}

export interface PurchaseCreateInput {
  purchased_at?: string | null
  items: PurchaseItemInput[]
}

export interface PurchaseItem {
  id: number
  product_id: number
  product_name: string
  base_unit: string
  commercial_unit: string | null
  conversion_factor: string
  commercial_quantity: string
  commercial_unit_price: string
  expiry_date?: string | null
}

export interface Purchase {
  id: number
  purchased_at: string
  items: PurchaseItem[]
}

// --- M10: Important Dates (Upcoming) ---

export interface UpcomingDate {
  id: number
  customer_id: number
  customer_name: string
  description: string
  recurring: boolean
  next_occurrence: string
  status: string
}

export interface UpcomingDatesList {
  items: UpcomingDate[]
  total: number
}

// --- M12: Auth ---

export type UserRole = 'admin' | 'operator'

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface UserProfile {
  id: number
  email: string
  full_name: string
  role: UserRole
}

export interface UserResponse {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface UserCreateInput {
  email: string
  password: string
  full_name: string
  role: UserRole
}

export interface UserUpdateInput {
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

