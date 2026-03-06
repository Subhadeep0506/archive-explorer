import { useThemeContext } from '@/context/ThemeContext';

// Re-export the context hook as useTheme for backward compatibility
export function useTheme() {
  return useThemeContext();
}
