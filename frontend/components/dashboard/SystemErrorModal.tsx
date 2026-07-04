"use client";

interface Props {
  message: string | null;
  onClose: () => void;
}

export default function SystemErrorModal({ message, onClose }: Props) {
  if (!message) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="max-w-lg w-full bg-zinc-900 border-2 border-sell rounded-2xl p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-xs font-bold uppercase tracking-widest text-sell/80 mb-2">
          El análisis no pudo completarse
        </p>
        <p className="text-sm text-zinc-300 leading-relaxed mb-4">
          Uno o más agentes fallaron durante la ejecución. Este es el error reportado:
        </p>
        <pre className="text-xs text-zinc-400 bg-zinc-950 border border-border rounded-lg p-3 mb-5 whitespace-pre-wrap break-words">
          {message}
        </pre>
        <button
          onClick={onClose}
          className="w-full bg-sell text-white font-semibold text-sm py-2 rounded-lg hover:opacity-90 transition-opacity"
        >
          Entendido
        </button>
      </div>
    </div>
  );
}
