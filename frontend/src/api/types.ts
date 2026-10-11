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
}

export interface Product extends ProductInput {
  id: number
  active: boolean
  reference_price?: string | null
  inventory_balance: string
  average_cost?: string | null
  created_at: string
  updated_at: string
}

export interface InventoryMovement {
  id: number
  product_id: number
  quantity: string
  type: 'ENTRY' | 'ADJUSTMENT'
  unit_cost?: string | null
  created_at: string
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

export interface Basket {
  id: number
  name: string
  template_id: number | null
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

