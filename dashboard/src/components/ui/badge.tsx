import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'border-border bg-panel text-foreground',
        active: 'border-transparent bg-status-active/15 text-status-active',
        suspended: 'border-transparent bg-status-suspended/15 text-status-suspended',
        offboarded: 'border-transparent bg-status-offboarded/15 text-status-offboarded',
        overdue: 'border-transparent bg-status-overdue/15 text-status-overdue',
        secondary: 'border-transparent bg-accent/10 text-accent',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
