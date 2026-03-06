import { useTheme } from "next-themes";
import { Toaster as Sonner, toast } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-slate-100 dark:group-[.toaster]:bg-slate-800 group-[.toaster]:text-slate-900 dark:group-[.toaster]:text-slate-100 group-[.toaster]:border-2 group-[.toaster]:border-slate-300 dark:group-[.toaster]:border-slate-600 group-[.toaster]:shadow-2xl",
          description:
            "group-[.toast]:text-slate-700 dark:group-[.toast]:text-slate-300",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton:
            "group-[.toast]:bg-slate-200 dark:group-[.toast]:bg-slate-700 group-[.toast]:text-slate-900 dark:group-[.toast]:text-slate-100",
          success:
            "group-[.toaster]:border-green-400 dark:group-[.toaster]:border-green-600 group-[.toaster]:bg-green-100 dark:group-[.toaster]:bg-green-800 group-[.toaster]:text-green-900 dark:group-[.toaster]:text-green-100",
          error:
            "group-[.toaster]:border-red-400 dark:group-[.toaster]:border-red-600 group-[.toaster]:bg-red-100 dark:group-[.toaster]:bg-red-800 group-[.toaster]:text-red-900 dark:group-[.toaster]:text-red-100",
          warning:
            "group-[.toaster]:border-yellow-400 dark:group-[.toaster]:border-yellow-600 group-[.toaster]:bg-yellow-100 dark:group-[.toaster]:bg-yellow-800 group-[.toaster]:text-yellow-900 dark:group-[.toaster]:text-yellow-100",
          info: "group-[.toaster]:border-blue-400 dark:group-[.toaster]:border-blue-600 group-[.toaster]:bg-blue-100 dark:group-[.toaster]:bg-blue-800 group-[.toaster]:text-blue-900 dark:group-[.toaster]:text-blue-100",
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
