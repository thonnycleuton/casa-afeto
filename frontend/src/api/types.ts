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
}

export interface Product extends ProductInput {
  id: number
  active: boolean
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
