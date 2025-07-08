import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface CardProps {
  icon: LucideIcon;
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function Card({ icon: Icon, title, children, className = '' }: CardProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 ${className}`}>
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100 flex items-center gap-2">
        <Icon className="w-5 h-5 text-blue-500" />
        {title}
      </h2>
      {children}
    </div>
  );
}