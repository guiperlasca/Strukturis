import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { PageResult } from "@/types/document";

interface DocumentSidebarProps {
  pages: PageResult[];
  currentPage: number;
  onPageSelect: (pageNumber: number) => void;
}

export const DocumentSidebar = ({ pages, currentPage, onPageSelect }: DocumentSidebarProps) => {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "bg-success";
    if (confidence >= 70) return "bg-primary";
    return "bg-destructive";
  };

  const getConfidenceBadgeVariant = (confidence: number) => {
    if (confidence >= 90) return "default";
    if (confidence >= 70) return "secondary";
    return "destructive";
  };

  return (
    <Sidebar className={cn(collapsed ? "w-14" : "w-64")} collapsible="icon">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            {!collapsed && "Páginas do Documento"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {pages.map((page) => (
                <SidebarMenuItem key={page.pageNumber}>
                  <SidebarMenuButton
                    onClick={() => onPageSelect(page.pageNumber)}
                    isActive={currentPage === page.pageNumber}
                    className={cn(
                      "relative",
                      currentPage === page.pageNumber && "bg-muted font-medium"
                    )}
                  >
                    <FileText className="h-4 w-4 flex-shrink-0" />
                    {!collapsed && (
                      <div className="flex flex-1 items-center justify-between">
                        <span>Página {page.pageNumber}</span>
                        <Badge
                          variant={getConfidenceBadgeVariant(page.confidence)}
                          className="ml-2 text-xs"
                        >
                          {page.confidence}%
                        </Badge>
                      </div>
                    )}
                    {/* Colored indicator bar */}
                    <div
                      className={cn(
                        "absolute left-0 top-0 h-full w-1",
                        getConfidenceColor(page.confidence)
                      )}
                    />
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
};
