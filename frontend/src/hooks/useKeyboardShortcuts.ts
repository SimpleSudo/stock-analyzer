import { useEffect } from 'react';

interface KeyboardShortcutsConfig {
  [key: string]: () => void;
}

export const useKeyboardShortcuts = (config: KeyboardShortcutsConfig, enabled = true) => {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Prevent shortcuts when typing in input/textarea
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      const key = event.key.toLowerCase();
      const ctrlKey = event.ctrlKey || event.metaKey; // Support Cmd on Mac
      const shiftKey = event.shiftKey;
      
      // Create key identifier
      let keyId = '';
      if (ctrlKey) keyId += 'ctrl+';
      if (shiftKey) keyId += 'shift+';
      keyId += key;

      // Execute corresponding action
      if (config[keyId]) {
        event.preventDefault(); // Prevent default browser behavior
        config[keyId]();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [config, enabled]);
};