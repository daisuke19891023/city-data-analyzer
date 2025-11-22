import type { ReactNode } from 'react';

function cn(...classes: Array<string | undefined>): string {
    return classes.filter(Boolean).join(' ');
}

type CardProps = {
    children: ReactNode;
    className?: string;
};

export function Card({ children, className }: CardProps): JSX.Element {
    return <div className={cn('ui-card', className)}>{children}</div>;
}

type CardHeaderProps = {
    children: ReactNode;
    className?: string;
};

export function CardHeader({
    children,
    className
}: CardHeaderProps): JSX.Element {
    return <div className={cn('ui-card__header', className)}>{children}</div>;
}

type CardTitleProps = {
    children: ReactNode;
    className?: string;
};

export function CardTitle({
    children,
    className
}: CardTitleProps): JSX.Element {
    return <h3 className={cn('ui-card__title', className)}>{children}</h3>;
}

type CardDescriptionProps = {
    children: ReactNode;
    className?: string;
};

export function CardDescription({
    children,
    className
}: CardDescriptionProps): JSX.Element {
    return <p className={cn('ui-card__description', className)}>{children}</p>;
}

type CardContentProps = {
    children: ReactNode;
    className?: string;
};

export function CardContent({
    children,
    className
}: CardContentProps): JSX.Element {
    return <div className={cn('ui-card__content', className)}>{children}</div>;
}
