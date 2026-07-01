import { useState } from "react";
import { ChevronsUpDown, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import { ARXIV_CS_CATEGORIES, type ArxivCategory } from "@/lib/categories";

interface CategoryMultiSelectProps {
    value: string[];
    onChange: (value: string[]) => void;
    placeholder?: string;
}

const grouped = ARXIV_CS_CATEGORIES.reduce<Record<string, ArxivCategory[]>>(
    (acc, cat) => {
        const prefix = cat.code.split(".")[0];
        (acc[prefix] ??= []).push(cat);
        return acc;
    },
    {},
);

const GROUP_LABELS: Record<string, string> = {
    cs: "Computer Science",
    stat: "Statistics",
    eess: "Electrical Engineering & Systems",
};

export function CategoryMultiSelect({
    value,
    onChange,
    placeholder = "Select categories...",
}: CategoryMultiSelectProps) {
    const [open, setOpen] = useState(false);

    const toggle = (code: string) => {
        onChange(
            value.includes(code)
                ? value.filter((v) => v !== code)
                : [...value, code],
        );
    };

    const remove = (code: string) => {
        onChange(value.filter((v) => v !== code));
    };

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className="w-full justify-between h-auto min-h-10 py-2"
                >
                    <div className="flex flex-wrap gap-1.5 flex-1">
                        {value.length > 0 ? (
                            value.map((code) => (
                                <Badge
                                    key={code}
                                    variant="secondary"
                                    className="gap-1"
                                >
                                    {code}
                                    <span
                                        role="button"
                                        tabIndex={0}
                                        className="rounded-full hover:bg-muted-foreground/20 p-0.5 cursor-pointer"
                                        onPointerDown={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                        }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            remove(code);
                                        }}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter" || e.key === " ") {
                                                e.stopPropagation();
                                                remove(code);
                                            }
                                        }}
                                    >
                                        <X className="h-3 w-3" />
                                    </span>
                                </Badge>
                            ))
                        ) : (
                            <span className="text-muted-foreground font-normal">
                                {placeholder}
                            </span>
                        )}
                    </div>
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
                <Command>
                    <CommandInput placeholder="Search categories..." />
                    <CommandList className="max-h-64">
                        <CommandEmpty>No categories found.</CommandEmpty>
                        {Object.entries(grouped).map(([prefix, categories]) => (
                            <CommandGroup
                                key={prefix}
                                heading={GROUP_LABELS[prefix] ?? prefix}
                            >
                                {categories.map((cat) => (
                                    <CommandItem
                                        key={cat.code}
                                        value={`${cat.code} ${cat.label}`}
                                        data-checked={value.includes(cat.code) || undefined}
                                        onSelect={() => toggle(cat.code)}
                                    >
                                        <span className="font-mono text-xs w-14 shrink-0">
                                            {cat.code}
                                        </span>
                                        <span className="truncate">
                                            {cat.label}
                                        </span>
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        ))}
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    );
}
