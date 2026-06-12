import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { DollarSign, Clock } from 'lucide-react';
import { formatCurrency } from './utils/helpers';
import type { DayBalance } from './pages/POSPageEnhanced';

export interface CashDrawerData {
  id: string;
  cashierId: string;
  date: string;
  openingBalance: number;
  closingBalance: number;
  transactions: number;
  status: 'open' | 'closed';
  createdAt: Date;
  closedAt?: Date;
}

interface CashDrawerProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  cashier: string;
  dayBalance: DayBalance;
  cashSalesToday: number;
  onOpenDay: (openingBalance: number) => void;
  // Closing is automatic (24h after opening); kept for interface compatibility.
  onCloseDay: (closingBalance: number) => void;
}

const DRAWER_DURATION_MS = 24 * 60 * 60 * 1000;

export function CashDrawer({
  isOpen,
  onOpenChange,
  cashier,
  dayBalance,
  cashSalesToday,
  onOpenDay
}: CashDrawerProps) {
  const [openingBalance, setOpeningBalance] = useState(dayBalance.openingBalance.toString());
  const expectedBalance = dayBalance.openingBalance + cashSalesToday;

  const handleOpenDrawer = (e: React.FormEvent) => {
    e.preventDefault();
    if (openingBalance && parseFloat(openingBalance) >= 0) {
      onOpenDay(parseFloat(openingBalance));
      onOpenChange(false);
    }
  };

  const today = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  // ---- Drawer CLOSED: prompt for opening balance only ----
  if (dayBalance.status === 'closed') {
    return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogTrigger asChild>
          <Button variant="outline" className="gap-2 w-full">
            <DollarSign className="w-4 h-4" />
            Open Cash Drawer
          </Button>
        </DialogTrigger>
        <DialogContent className="bg-white border-gray-200 max-w-md">
          <DialogHeader>
            <DialogTitle>Open Cash Drawer for Today</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleOpenDrawer} className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-600 mb-2">Date</p>
              <p className="font-semibold text-gray-900">{today}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">Cashier</p>
              <p className="font-semibold text-gray-900">{cashier}</p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-600">Opening Balance</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">KSh </span>
                <Input
                  type="number"
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                  className="pl-12 bg-white border-gray-300"
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  required
                />
              </div>
            </div>
            <div className="flex items-start gap-2 text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
              <Clock className="w-4 h-4 mt-0.5 shrink-0" />
              <span>The drawer will close automatically 24 hours after opening.</span>
            </div>
            <Button type="submit" className="w-full bg-green-600 hover:bg-green-700">
              Open Drawer
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    );
  }

  // ---- Drawer OPEN: informational only, closes automatically ----
  const autoCloseAt = dayBalance.openedAt
    ? new Date(dayBalance.openedAt + DRAWER_DURATION_MS)
    : null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button className="gap-2 bg-green-600 hover:bg-green-700 w-full">
          <DollarSign className="w-4 h-4" />
          Drawer Open
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-white border-gray-200 max-w-md">
        <DialogHeader>
          <DialogTitle>Cash Drawer Status</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Opening Balance</p>
                  <p className="text-lg font-bold text-gray-900">{formatCurrency(dayBalance.openingBalance)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 mb-1">Today's Cash Sales</p>
                  <p className="text-lg font-bold text-blue-600">{formatCurrency(cashSalesToday)}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-gray-600 mb-1">Expected Balance</p>
                  <p className="text-lg font-bold text-gray-900">{formatCurrency(expectedBalance)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            <Clock className="w-4 h-4 mt-0.5 shrink-0" />
            <span>
              This drawer closes automatically
              {autoCloseAt ? ` on ${autoCloseAt.toLocaleString()}` : ' 24 hours after opening'}.
              No manual closing balance is required.
            </span>
          </div>

          <Button variant="outline" className="w-full" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
