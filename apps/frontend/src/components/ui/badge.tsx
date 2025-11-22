import type { ReactNode } from 'react';

function cn(...classes: Array<string | undefined>): string {
    return classes.filter(Boolean).join(' ');
}

type BadgeVariant = 'neutral' | 'success' | 'warning' | 'accent';

type BadgeProps = {
    children: ReactNode;
    variant?: BadgeVariant;
    className?: string;
};

export function Badge({
    children,
    variant = 'neutral',
    className
}: BadgeProps): JSX.Element {
    const variantClass: Record<BadgeVariant, string> = {
        neutral: '',
        success: 'ui-badge--success',
        warning: 'ui-badge--warning',
        accent: 'ui-badge--accent'
    };

    return (
        <span className={cn('ui-badge', variantClass[variant], className)}>
            {children}
        </span>
    );
}
