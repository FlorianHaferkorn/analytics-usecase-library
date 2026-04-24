'use client';

import { useState } from 'react';

interface WizardProps {
  isOpen: boolean;
  onClose: () => void;
}

type Step = 1 | 2 | 3;

export function Wizard({ isOpen, onClose }: WizardProps) {
  const [step, setStep] = useState<Step>(1);
  const [elementType, setElementType] = useState<string>('');
  const [description, setDescription] = useState<string>('');

  const handleNext = () => {
    if (step < 3) {
      setStep((step + 1) as Step);
    }
  };

  const handlePrev = () => {
    if (step > 1) {
      setStep((step - 1) as Step);
    }
  };

  const handleClose = () => {
    setStep(1);
    setElementType('');
    setDescription('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 z-modal flex items-center justify-center"
      onClick={handleClose}
    >
      <div
        className="w-full max-w-md max-h-96 bg-panel rounded-lg shadow-lg border border-border flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b border-border px-6 py-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground font-display">New Element</h2>
          <button
            onClick={handleClose}
            className="p-1 rounded text-foreground-subtle hover:bg-hover transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
              <line x1="2" y1="2" x2="14" y2="14" strokeWidth="1.5" />
              <line x1="14" y1="2" x2="2" y2="14" strokeWidth="1.5" />
            </svg>
          </button>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-1 px-6 pt-4">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex-1 h-1 rounded transition-colors ${
                s <= step ? 'bg-accent' : 'bg-line'
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 px-6 py-6 flex flex-col gap-4">
          {step === 1 && (
            <>
              <div>
                <label className="block text-xs font-semibold text-foreground-subtle mb-2">
                  What do you want to create?
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {['KPI', 'Data Source', 'Action Code', 'Use Case'].map((type) => (
                    <button
                      key={type}
                      onClick={() => setElementType(type)}
                      className={`px-3 py-2 rounded text-xs font-medium transition-colors ${
                        elementType === type
                          ? 'bg-accent text-accent-ink'
                          : 'bg-bg text-foreground-muted hover:bg-hover border border-line'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div>
                <label className="block text-xs font-semibold text-foreground-subtle mb-2">
                  Describe your {elementType?.toLowerCase()}
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter a description. AI will draft the details."
                  className="w-full px-3 py-2 rounded bg-bg text-foreground text-xs border border-line focus:outline-none focus:border-accent resize-none h-24"
                />
              </div>
              <div className="p-3 bg-bg rounded border border-line">
                <p className="text-xs text-foreground-subtle">
                  AI will draft a {elementType?.toLowerCase()} based on your description.
                </p>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <div>
                <label className="block text-xs font-semibold text-foreground-subtle mb-2">
                  Review & Save
                </label>
                <div className="p-3 bg-bg rounded border border-line">
                  <p className="text-xs text-foreground-subtle mb-2">
                    <strong>Type:</strong> {elementType}
                  </p>
                  <p className="text-xs text-foreground-subtle">
                    <strong>Description:</strong> {description}
                  </p>
                </div>
              </div>
              <div className="p-3 bg-positive-soft rounded border border-positive">
                <p className="text-xs text-foreground">
                  When you click Save, this {elementType?.toLowerCase()} will be created.
                </p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border px-6 py-3 bg-bg-2 flex items-center justify-between gap-2">
          <div className="text-xs text-foreground-subtle">
            Step {step} of 3
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrev}
              disabled={step === 1}
              className="px-3 py-2 rounded-lg border border-line text-xs font-medium text-foreground-muted hover:bg-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Back
            </button>
            {step < 3 ? (
              <button
                onClick={handleNext}
                disabled={!elementType || (step === 2 && !description)}
                className="px-3 py-2 rounded-lg bg-accent text-accent-ink text-xs font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleClose}
                className="px-3 py-2 rounded-lg bg-accent text-accent-ink text-xs font-medium hover:opacity-90 transition-opacity"
              >
                Save
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
