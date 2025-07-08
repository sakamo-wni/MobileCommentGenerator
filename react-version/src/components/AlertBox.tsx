import React from 'react';
import { AlertTriangle, XCircle, Info } from 'lucide-react';

interface AlertBoxProps {
  type: 'warning' | 'error' | 'info';
  title?: string;
  children: React.ReactNode;
}

export function AlertBox({ type, title, children }: AlertBoxProps) {
  const styles = {
    warning: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-200 dark:border-yellow-800',
      text: 'text-yellow-800 dark:text-yellow-200',
      icon: AlertTriangle,
      iconColor: 'text-yellow-600 dark:text-yellow-400'
    },
    error: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-800 dark:text-red-200',
      icon: XCircle,
      iconColor: 'text-red-600 dark:text-red-400'
    },
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-800 dark:text-blue-200',
      icon: Info,
      iconColor: 'text-blue-600 dark:text-blue-400'
    }
  };

  const { bg, border, text, icon: Icon, iconColor } = styles[type];

  return (
    <div className={`${bg} border ${border} rounded-lg p-4 mb-6`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${iconColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          {title && (
            <h3 className={`font-medium ${text} mb-1`}>{title}</h3>
          )}
          <div className={`text-sm ${text}`}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}