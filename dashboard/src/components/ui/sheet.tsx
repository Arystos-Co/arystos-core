import * as React from 'react'

import { cn } from '@/lib/utils'

function Sheet({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

function SheetContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn('fixed right-0 top-0 z-50 h-full w-full max-w-md border-l border-border bg-panel p-6 shadow-soft', className)}>{children}</div>
}

export { Sheet, SheetContent }
