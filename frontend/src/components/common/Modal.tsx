import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
  maxWidth?: 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl';
  maxHeight?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  showCloseButton?: boolean;
  closeOnBackdropClick?: boolean;
  closeOnEscape?: boolean;
}

const MAX_WIDTH_MAP: Record<string, string> = {
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  '3xl': 'max-w-3xl',
  '4xl': 'max-w-4xl', // ~896px
  '5xl': 'max-w-5xl', // ~1024px
  '6xl': 'max-w-6xl', // ~1152px
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  badge,
  icon,
  maxWidth = '4xl',
  maxHeight = 'max-h-[88vh]',
  children,
  actions,
  showCloseButton = true,
  closeOnBackdropClick = true,
  closeOnEscape = true,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Prevent background scrolling while modal is open
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Handle Escape key
    const handleKeyDown = (e: KeyboardEvent) => {
      if (closeOnEscape && e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, closeOnEscape, onClose]);

  if (!isOpen) return null;

  const widthClass = MAX_WIDTH_MAP[maxWidth] || 'max-w-4xl';

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 bg-black/75 backdrop-blur-[2px] transition-all duration-150 animate-in fade-in"
      onClick={() => {
        if (closeOnBackdropClick) onClose();
      }}
    >
      <div
        ref={modalRef}
        onClick={(e) => e.stopPropagation()}
        className={`w-full ${widthClass} ${maxHeight} flex flex-col rounded-2xl bg-[#0c1324] border border-slate-700/70 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150`}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-slate-800 bg-[#0e162a] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 overflow-hidden">
            {icon && (
              <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 shrink-0">
                {icon}
              </div>
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h3 className="text-base font-bold text-white font-sans truncate">
                  {title}
                </h3>
                {badge && <div>{badge}</div>}
              </div>
              {subtitle && (
                <p className="text-xs text-slate-400 mt-0.5 truncate font-sans">
                  {subtitle}
                </p>
              )}
            </div>
          </div>

          {showCloseButton && (
            <button
              onClick={onClose}
              aria-label="Close dialog"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer shrink-0 ml-2"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 md:p-6 space-y-5 text-slate-200">
          {children}
        </div>

        {/* Modal Footer (Optional) */}
        {actions && (
          <div className="px-5 py-3.5 border-t border-slate-800 bg-[#0e162a] flex items-center justify-between shrink-0 gap-3">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};
