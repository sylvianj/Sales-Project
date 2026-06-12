import { useEffect, useMemo, useState } from 'react';
import { LoginPage } from './components/auth/LoginPage';
import { Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { Dashboard } from './components/pages/Dashboard';
import { POSPage } from './components/pages/POSPageEnhanced';
import { ProductsPageEnhanced } from './components/pages/ProductsPageEnhanced';
import { InventoryPage } from './components/pages/InventoryPage';
import { CustomersPage } from './components/pages/CustomersPage';
import { InvoicesPage } from './components/pages/InvoicesPage';
import { ProcurementPage } from './components/pages/ProcurementPage';
import { ExpensesPage } from './components/pages/ExpensesPage';
import { ReportsPage } from './components/pages/ReportsPage';
import { UsersPage } from './components/pages/UsersPage';
import { SettingsPage } from './components/pages/SettingsPage';
import {
  adjustInventory,
  approveUser,
  createProduct,
  createCustomer,
  createSale,
  createSupplier,
  createUser,
  deactivateUser,
  deleteProduct,
  downloadProductImportTemplate,
  importProductsExcel,
  loadCurrentUser,
  loadCustomers,
  loadProducts,
  loadSales,
  loadSuppliers,
  loadUsers,
  login,
  logout,
  normalizeRole,
  updateProduct,
  updateUser,
  verifyTwoFactor,
  type BackendCustomer,
  type BackendSupplier,
  type BackendUser
} from './services/api';
import type { UserRole } from './types/auth';
import type { BusinessExpense, StockMovement, SupplierOrderInvoice } from './types/supplierOrder';
import type { CompletedSale, DayBalance, POSProduct } from './components/pages/POSPageEnhanced';
import type { Product } from './components/pages/ProductsPageEnhanced';
import type { QuickActionId } from './components/QuickActions';

const todayKey = () => new Date().toISOString().slice(0, 10);

const initialDayBalance: DayBalance = {
  date: todayKey(),
  openingBalance: 0,
  closingBalance: null,
  status: 'closed',
  openedAt: null
};

// Cash drawer auto-closes 24 hours after it is opened.
const DRAWER_DURATION_MS = 24 * 60 * 60 * 1000;
const DRAWER_STORAGE_KEY = 'pos_day_balance';

// Restore the drawer across page reloads; auto-close if 24h already elapsed.
function loadDayBalance(): DayBalance {
  try {
    const raw = localStorage.getItem(DRAWER_STORAGE_KEY);
    if (raw) {
      const saved = JSON.parse(raw) as DayBalance;
      if (saved.status === 'open' && saved.openedAt && Date.now() - saved.openedAt >= DRAWER_DURATION_MS) {
        return { ...saved, status: 'closed', closingBalance: saved.openingBalance, openedAt: null };
      }
      return saved;
    }
  } catch {
    /* ignore corrupt storage */
  }
  return initialDayBalance;
}

export function App() {
  const [activeItem, setActiveItem] = useState('dashboard');
  const [currentUser, setCurrentUser] = useState<BackendUser | null>(null);
  const [isBooting, setIsBooting] = useState(true);
  const [products, setProducts] = useState<POSProduct[]>([]);
  const [completedSales, setCompletedSales] = useState<CompletedSale[]>([]);
  const [customers, setCustomers] = useState<BackendCustomer[]>([]);
  const [suppliers, setSuppliers] = useState<BackendSupplier[]>([]);
  const [users, setUsers] = useState<BackendUser[]>([]);
  const [stockMovements, setStockMovements] = useState<StockMovement[]>([]);
  const [supplierInvoices, setSupplierInvoices] = useState<SupplierOrderInvoice[]>([]);
  const [expenses, setExpenses] = useState<BusinessExpense[]>([]);
  const [dayBalance, setDayBalance] = useState<DayBalance>(loadDayBalance);
  const [openAddCustomerSignal, setOpenAddCustomerSignal] = useState(0);
  const [openAddInventorySignal, setOpenAddInventorySignal] = useState(0);
  const [openNewInvoiceSignal, setOpenNewInvoiceSignal] = useState(0);
  const [loadError, setLoadError] = useState('');

  const userRole: UserRole = normalizeRole(currentUser?.role);
  const userName = currentUser?.username || 'User';

  const cashSalesToday = useMemo(() => {
    const date = todayKey();
    return completedSales
      .filter(sale => sale.timestamp.toISOString().slice(0, 10) === date)
      .reduce((sum, sale) => sum + sale.cashAmount, 0);
  }, [completedSales]);

  // Persist the drawer so it (and its 24h timer) survives page reloads.
  useEffect(() => {
    try {
      localStorage.setItem(DRAWER_STORAGE_KEY, JSON.stringify(dayBalance));
    } catch {
      /* ignore */
    }
  }, [dayBalance]);

  // Auto-close the drawer exactly 24 hours after it was opened.
  useEffect(() => {
    if (dayBalance.status !== 'open' || !dayBalance.openedAt) return;
    const closeDrawer = () => setDayBalance(prev =>
      prev.status === 'open'
        ? { ...prev, status: 'closed', closingBalance: prev.openingBalance + cashSalesToday, openedAt: null }
        : prev
    );
    const remaining = dayBalance.openedAt + DRAWER_DURATION_MS - Date.now();
    if (remaining <= 0) {
      closeDrawer();
      return;
    }
    const timer = setTimeout(closeDrawer, remaining);
    return () => clearTimeout(timer);
  }, [dayBalance.status, dayBalance.openedAt, cashSalesToday]);

  const refreshBackendData = async () => {
    setLoadError('');
    try {
      const [nextProducts, nextSales, nextUsers, nextCustomers, nextSuppliers] = await Promise.all([
        loadProducts(),
        loadSales(),
        loadUsers(),
        loadCustomers(),
        loadSuppliers()
      ]);
      setProducts(nextProducts);
      setCompletedSales(nextSales);
      setUsers(nextUsers);
      setCustomers(nextCustomers);
      setSuppliers(nextSuppliers);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Could not load backend data.');
    }
  };

  useEffect(() => {
    let isMounted = true;

    loadCurrentUser()
      .then(user => {
        if (!isMounted) return;
        setCurrentUser(user);
        if (user) {
          refreshBackendData();
        }
      })
      .finally(() => {
        if (isMounted) setIsBooting(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogin = async (username: string, password: string, role: UserRole) => {
    const result = await login(username, password, role);
    if (result.user && !result.twoFactorRequired) {
      setCurrentUser(result.user);
      await refreshBackendData();
    }
    return result;
  };

  const handleVerifyTwoFactor = async (username: string, code: string, role: UserRole) => {
    const result = await verifyTwoFactor(username, code, role);
    if (result.user) {
      setCurrentUser(result.user);
      await refreshBackendData();
    }
    return result;
  };

  const handleLogout = async () => {
    await logout();
    setCurrentUser(null);
    setProducts([]);
    setCompletedSales([]);
    setCustomers([]);
    setSuppliers([]);
    setUsers([]);
    setActiveItem('dashboard');
  };

  const handleCreateProduct = async (product: Product) => {
    const saved = await createProduct(product);
    setProducts(previous => [saved, ...previous.filter(item => item.id !== saved.id)]);
  };

  const handleUpdateProduct = async (product: Product) => {
    const saved = await updateProduct(product);
    setProducts(previous => previous.map(item => item.id === saved.id ? saved : item));
  };

  const handleDeleteProduct = async (productId: string) => {
    await deleteProduct(productId);
    setProducts(previous => previous.filter(item => item.id !== productId));
  };

  const handleTransactionComplete = async (sale: CompletedSale) => {
    try {
      const savedSale = await createSale(sale);
      setCompletedSales(previous => [savedSale, ...previous.filter(item => item.id !== sale.id)]);
      setProducts(await loadProducts());
      window.dispatchEvent(new Event('pos:notifications-changed'));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Sale could not be saved because payment was not confirmed.';
      setLoadError(message);
      throw new Error(message);
    }
  };

  const handleStockAdjustment = async (productId: string, type: 'in' | 'out', quantity: number, reason: string) => {
    const product = products.find(item => item.id === productId);
    try {
      const result = await adjustInventory({
        product_id: productId,
        movement_type: type === 'in' ? 'stock_in' : 'stock_out',
        quantity,
        note: reason,
        reference: `UI-${Date.now()}`
      });

      if (result.product) {
        setProducts(previous => previous.map(item => item.id === productId ? result.product! : item));
      }

      setStockMovements(previous => [{
        id: String(result.movement?.id || Date.now()),
        productId,
        productName: product?.name || result.product?.name || 'Item',
        item: product?.name || result.product?.name || 'Item',
        type,
        quantity: type === 'in' ? quantity : -quantity,
        reason,
        date: todayKey()
      }, ...previous]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Stock adjustment could not be saved.';
      setLoadError(message);
      throw new Error(message);
    }
  };

  const handleQuickAction = (action: QuickActionId) => {
    if (action === 'new-sale') setActiveItem('pos');
    if (action === 'add-product') {
      // Products are added from Inventory (the Products page is read-only).
      setActiveItem('inventory');
      setOpenAddInventorySignal(signal => signal + 1);
    }
    if (action === 'add-customer') {
      setActiveItem('customers');
      setOpenAddCustomerSignal(signal => signal + 1);
    }
    if (action === 'quick-invoice') {
      setActiveItem('invoices');
      setOpenNewInvoiceSignal(signal => signal + 1);
    }
  };

  const handleCreateSupplierOrder = (invoice: Omit<SupplierOrderInvoice, 'id'>) => {
    setSupplierInvoices(previous => [{ ...invoice, id: String(Date.now()) }, ...previous]);
  };

  const content = () => {
    switch (activeItem) {
      case 'pos':
        return (
          <POSPage
            products={products}
            dayBalance={dayBalance}
            onTransactionComplete={handleTransactionComplete}
            onOpenDay={(openingBalance) => setDayBalance({ date: todayKey(), openingBalance, closingBalance: null, status: 'open', openedAt: Date.now() })}
            onCloseDay={(closingBalance) => setDayBalance(previous => ({ ...previous, closingBalance, status: 'closed', openedAt: null }))}
            cashSalesToday={cashSalesToday}
          />
        );
      case 'products':
        return (
          <ProductsPageEnhanced
            products={products}
            readOnly
          />
        );
      case 'inventory':
        return (
          <InventoryPage
            products={products}
            stockMovements={stockMovements}
            openAddItemSignal={openAddInventorySignal}
            onStockAdjustment={handleStockAdjustment}
            onAddItem={handleCreateProduct}
            onBulkImportItems={async (file) => {
              const result = await importProductsExcel(file);
              await refreshBackendData();
              return result;
            }}
            onDownloadImportTemplate={downloadProductImportTemplate}
          />
        );
      case 'customers':
        return (
          <CustomersPage
            completedSales={completedSales}
            backendCustomers={customers}
            openAddCustomerSignal={openAddCustomerSignal}
            onCustomerCreated={async (customer) => {
              const saved = await createCustomer(customer);
              setCustomers(previous => [saved, ...previous.filter(item => item.id !== saved.id)]);
            }}
          />
        );
      case 'invoices':
        return (
          <InvoicesPage
            completedSales={completedSales}
            supplierInvoices={supplierInvoices}
            openNewInvoiceSignal={openNewInvoiceSignal}
            onStartSale={() => setActiveItem('pos')}
            onRecordSupplierOrder={() => setActiveItem('procurement')}
          />
        );
      case 'procurement':
        return (
          <ProcurementPage
            products={products}
            backendSuppliers={suppliers}
            supplierInvoices={supplierInvoices}
            onSupplierOrderCreated={handleCreateSupplierOrder}
            onSupplierCreated={async (supplier) => {
              const saved = await createSupplier(supplier);
              setSuppliers(previous => [saved, ...previous.filter(item => item.id !== saved.id)]);
            }}
          />
        );
      case 'expenses':
        return <ExpensesPage expenses={expenses} onExpenseCreated={(expense) => setExpenses(previous => [{ ...expense, id: String(Date.now()) }, ...previous])} />;
      case 'reports':
        return <ReportsPage products={products} completedSales={completedSales} expenses={expenses} supplierInvoices={supplierInvoices} dayBalance={dayBalance} />;
      case 'users':
        return (
          <UsersPage
            users={users}
            onCreateUser={async (user) => {
              const saved = await createUser(user);
              setUsers(previous => [saved, ...previous]);
            }}
            onUpdateUser={async (id, user) => {
              const saved = await updateUser(id, user);
              setUsers(previous => previous.map(item => item.id === id ? { ...item, ...saved } : item));
            }}
            onDeactivateUser={async (id) => {
              await deactivateUser(id);
              setUsers(previous => previous.map(item => item.id === id ? { ...item, is_active: false } : item));
            }}
            onApproveUser={async (id) => {
              await approveUser(id);
              setUsers(previous => previous.map(item => item.id === id ? { ...item, is_active: true } : item));
            }}
          />
        );
      case 'settings':
        return <SettingsPage />;
      default:
        return (
          <Dashboard
            products={products}
            completedSales={completedSales}
            dayBalance={dayBalance}
            cashSalesToday={cashSalesToday}
            customerCount={customers.length}
            supplierCount={suppliers.length || new Set(supplierInvoices.map(invoice => invoice.supplierName)).size}
            supplierInvoiceCount={supplierInvoices.length}
            userRole={userRole}
            onQuickAction={handleQuickAction}
          />
        );
    }
  };

  if (isBooting) {
    return <div className="flex min-h-screen items-center justify-center text-gray-600">Loading...</div>;
  }

  if (!currentUser) {
    return <LoginPage onLogin={handleLogin} onVerifyTwoFactor={handleVerifyTwoFactor} />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar
        activeItem={activeItem}
        onItemClick={setActiveItem}
        onLogout={handleLogout}
        userRole={userRole}
        userName={userName}
      />
      <div className="min-w-0 flex-1">
        <TopHeader />
        <main className="p-4 sm:p-8">
          {loadError && (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {loadError}
            </div>
          )}
          {content()}
        </main>
      </div>
    </div>
  );
}
