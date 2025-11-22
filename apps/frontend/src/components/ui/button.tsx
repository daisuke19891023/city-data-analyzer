import type { ComponentPropsWithoutRef } from 'react';

function cn(...classes: Array<string | undefined>): string {
    return classes.filter(Boolean).join(' ');
}

type ButtonVariant = 'primary' | 'ghost' | 'secondary';
type ButtonSize = 'md' | 'sm';

type ButtonProps = {
    variant?: ButtonVariant;
    size?: ButtonSize;
    className?: string;
} & ComponentPropsWithoutRef<'button'>;

export function Button({
    variant = 'primary',
    size = 'md',
    className,
    type = 'button',
    ...props
}: ButtonProps): JSX.Element {
    const variantClass: Record<ButtonVariant, string> = {
        primary: '',
        ghost: 'ui-button--ghost',
        secondary: 'ui-button--secondary'
    };

    const sizeClass: Record<ButtonSize, string> = {
        md: '',
        sm: 'ui-button--sm'
    };

    return (
        <button
            type={type}
            className={cn(
                'ui-button',
                variantClass[variant],
                sizeClass[size],
                className
            )}
            {...props}
        />
    );
}
