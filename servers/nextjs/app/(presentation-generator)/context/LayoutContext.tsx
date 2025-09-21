"use client";
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import dynamic from "next/dynamic";
import { toast } from "sonner";
import * as z from "zod";
import { useDispatch } from "react-redux";
import { setLayoutLoading } from "@/store/slices/presentationGeneration";
import * as Babel from "@babel/standalone";
import * as Recharts from "recharts";
export interface LayoutInfo {
  id: string;
  name?: string;
  description?: string;
  json_schema: any;
  groupName: string;
}
export interface FullDataInfo {
  name: string;
  component: React.ComponentType<any>;
  schema: any;
  sampleData: any;
  fileName: string;
  groupName: string;
  layoutId: string;
}

export interface GroupSetting {
  description: string;
  ordered: boolean;
  default?: boolean;
}

export interface GroupedLayoutsResponse {
  groupName: string;
  files: string[];
  settings: GroupSetting | null;
}

export interface LayoutData {
  layoutsById: Map<string, LayoutInfo>;
  layoutsByGroup: Map<string, Set<string>>;
  groupSettings: Map<string, GroupSetting>;
  fileMap: Map<string, { fileName: string; groupName: string }>;
  groupedLayouts: Map<string, LayoutInfo[]>;
  layoutSchema: LayoutInfo[];
  fullDataByGroup: Map<string, FullDataInfo[]>;
}

export interface LayoutContextType {
  getLayoutById: (layoutId: string) => LayoutInfo | null;
  getLayoutByIdAndGroup: (
    layoutId: string,
    groupName: string
  ) => LayoutInfo | null;
  getLayoutsByGroup: (groupName: string) => LayoutInfo[];
  getGroupSetting: (groupName: string) => GroupSetting | null;
  getAllGroups: () => string[];
  getAllLayouts: () => LayoutInfo[];
  getFullDataByGroup: (groupName: string) => FullDataInfo[];
  loading: boolean;
  error: string | null;
  getLayout: (layoutId: string) => React.ComponentType<{ data: any }> | null;
  isPreloading: boolean;
  cacheSize: number;
  refetch: () => Promise<void>;
  getCustomTemplateFonts: (presentationId: string) => string[] | null;
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

const layoutCache = new Map<string, React.ComponentType<{ data: any }>>();

const createCacheKey = (groupName: string, fileName: string): string =>
  `${groupName}/${fileName}`;

// Extract Babel compilation logic into a utility function
const compileCustomLayout = (layoutCode: string, React: any, z: any) => {

  const cleanCode = layoutCode
    .replace(/import\s+React\s+from\s+'react';?/g, "")
    .replace(/import\s*{\s*z\s*}\s*from\s+'zod';?/g, "")
    .replace(/import\s+.*\s+from\s+['"]zod['"];?/g, "")
    // remove every zod import (any style)
    .replace(/import\s+.*\s+from\s+['"]zod['"];?/g, "")
    .replace(/const\s+[^=]*=\s*require\(['"]zod['"]\);?/g, "")
    .replace(/typescript/g, "")
  const compiled = Babel.transform(cleanCode, {
    presets: [
      ["react", { runtime: "classic" }],
      ["typescript", { isTSX: true, allExtensions: true }],
    ],
    sourceType: "script",
  }).code;

  const factory = new Function(
    "React",
    "_z",
    "Recharts",
    `
    const z = _z;
    // Expose commonly used Recharts components to compiled layouts
        const { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ComposedChart, ScatterChart, Scatter, FunnelChart, Funnel, TreemapChart, Treemap, SankeyChart, Sankey, RadialBarChart, RadialBar, ReferenceLine, ReferenceDot, ReferenceArea, Brush, ErrorBar, LabelList, Label } = Recharts || {};

      ${compiled}

      /* everything declared in the string is in scope here */
      return {
        __esModule: true,   
        default: typeof dynamicSlideLayout !== 'undefined' ? dynamicSlideLayout : (typeof DefaultLayout !== 'undefined' ? DefaultLayout : undefined),
        layoutName,
        layoutId,
        layoutDescription,
        Schema
      };
    `
  );

  return factory(React, z, Recharts);
};

export const LayoutProvider: React.FC<{
  children: ReactNode;
}> = ({ children }) => {
  const [layoutData, setLayoutData] = useState<LayoutData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPreloading, setIsPreloading] = useState(false);
  const [customTemplateFonts, setCustomTemplateFonts] = useState<Map<string, string[]>>(new Map());
  const dispatch = useDispatch();

  const buildData = async (groupedLayoutsData: GroupedLayoutsResponse[]) => {
    const layouts: LayoutInfo[] = [];

    const layoutsById = new Map<string, LayoutInfo>();
    const layoutsByGroup = new Map<string, Set<string>>();
    const groupSettingsMap = new Map<string, GroupSetting>();
    const fileMap = new Map<string, { fileName: string; groupName: string }>();
    const groupedLayouts = new Map<string, LayoutInfo[]>();
    const fullDataByGroup = new Map<string, FullDataInfo[]>();

    // Start preloading process
    setIsPreloading(true);

    try {
      for (const groupData of groupedLayoutsData) {
        // Initialize group
        if (!layoutsByGroup.has(groupData.groupName)) {
          layoutsByGroup.set(groupData.groupName, new Set());
        }

        fullDataByGroup.set(groupData.groupName, []);

        // group settings or default settings
        const settings = groupData.settings || {
          description: `${groupData.groupName} presentation layouts`,
          ordered: false,
          default: false,
        };

        groupSettingsMap.set(groupData.groupName, settings);
        const groupLayouts: LayoutInfo[] = [];
        const groupFullData: FullDataInfo[] = [];

        for (const fileName of groupData.files) {
          try {
            const file = fileName.replace(".tsx", "").replace(".ts", "");

            const module = await import(
              `@/presentation-templates/${groupData.groupName}/${file}`
            );

            if (!module.default) {
              toast.error(`${file} has no default export`, {
                description:
                  "Please ensure the layout file exports a default component",
              });
              console.warn(`❌ ${file} has no default export`);
              continue;
            }

            if (!module.Schema) {
              toast.error(`${file} has no Schema export`, {
                description: "Please ensure the layout file exports a Schema",
              });
              console.warn(`❌ ${file} has no Schema export`);
              continue;
            }

            // Cache the layout component immediately after import
            const cacheKey = createCacheKey(groupData.groupName, fileName);
            if (!layoutCache.has(cacheKey)) {
              layoutCache.set(cacheKey, module.default);
            }

            const originalLayoutId =
              module.layoutId || file.toLowerCase().replace(/layout$/, "");
            const uniqueKey = `${groupData.groupName}:${originalLayoutId}`;
            const layoutName =
              module.layoutName || file.replace(/([A-Z])/g, " $1").trim();
            const layoutDescription =
              module.layoutDescription ||
              `${layoutName} layout for presentations`;

            const jsonSchema = z.toJSONSchema(module.Schema, {
              override: (ctx) => {
                delete ctx.jsonSchema.default;
              },
            });

            const layout: LayoutInfo = {
              id: uniqueKey,
              name: layoutName,
              description: layoutDescription,
              json_schema: jsonSchema,
              groupName: groupData.groupName,
            };

            const sampleData = module.Schema.parse({});
            const fullData: FullDataInfo = {
              name: layoutName,
              component: module.default,
              schema: jsonSchema,
              sampleData: sampleData,
              fileName,
              groupName: groupData.groupName,
              layoutId: uniqueKey,
            };
            groupFullData.push(fullData);

            layoutsById.set(uniqueKey, layout);
            layoutsByGroup.get(groupData.groupName)!.add(uniqueKey);
            fileMap.set(uniqueKey, {
              fileName,
              groupName: groupData.groupName,
            });
            groupLayouts.push(layout);
            layouts.push(layout);
          } catch (error) {
            console.error(
              `💥 Error extracting schema for ${fileName} from ${groupData.groupName}:`,
              error
            );
          }
        }

        fullDataByGroup.set(groupData.groupName, groupFullData);
        // Cache grouped layouts
        groupedLayouts.set(groupData.groupName, groupLayouts);
      }
    } catch (err: any) {
      console.error("Compilation error:", err);
    }

    return {
      layoutsById,
      layoutsByGroup,
      groupSettings: groupSettingsMap,
      fileMap,
      groupedLayouts,
      layoutSchema: layouts,
      fullDataByGroup,
    };
  };

  const loadLayouts = async () => {
    try {
      setLoading(true);
      setError(null);
      dispatch(setLayoutLoading(true));

      const layoutResponse = await fetch("/api/templates");

      if (!layoutResponse.ok) {
        throw new Error(
          `Failed to fetch layouts: ${layoutResponse.statusText}`
        );
      }

      const groupedLayoutsData: GroupedLayoutsResponse[] =
        await layoutResponse.json();

      if (!groupedLayoutsData || groupedLayoutsData.length === 0) {
        setError("No layout groups found");
        return;
      }

      const data = await buildData(groupedLayoutsData);
      const customLayouts = await LoadCustomLayouts();
      setIsPreloading(false);
      const combinedData = {
        layoutsById: mergeMaps(data.layoutsById, customLayouts.layoutsById),
        layoutsByGroup: mergeMaps(
          data.layoutsByGroup,
          customLayouts.layoutsByGroup
        ),
        groupSettings: mergeMaps(
          data.groupSettings,
          customLayouts.groupSettings
        ),
        fileMap: mergeMaps(data.fileMap, customLayouts.fileMap),
        groupedLayouts: mergeMaps(
          data.groupedLayouts,
          customLayouts.groupedLayouts
        ),
        layoutSchema: [...data.layoutSchema, ...customLayouts.layoutSchema],
        fullDataByGroup: mergeMaps(
          data.fullDataByGroup,
          customLayouts.fullDataByGroup
        ),
      };

      setLayoutData(combinedData);

      // The preloading is now handled within buildData
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load layouts";
      setError(errorMessage);
      console.error("💥 Error loading layouts:", err);
    } finally {
      dispatch(setLayoutLoading(false));
      setLoading(false);
    }
  };

  function mergeMaps<K, V>(map1: Map<K, V>, map2: Map<K, V>): Map<K, V> {
    const merged = new Map(map1);
    map2.forEach((value, key) => {
      merged.set(key, value);
    });
    return merged;
  }

  const LoadCustomLayouts = async () => {
    const layouts: LayoutInfo[] = [];
    const layoutsById = new Map<string, LayoutInfo>();
    const layoutsByGroup = new Map<string, Set<string>>();
    const groupSettingsMap = new Map<string, GroupSetting>();
    const fileMap = new Map<string, { fileName: string; groupName: string }>();
    const groupedLayouts = new Map<string, LayoutInfo[]>();
    const fullDataByGroup = new Map<string, FullDataInfo[]>();
    try {
      const customGroupResponse = await fetch(
        "/api/v1/ppt/template-management/summary"
      );
      const customGroupData = await customGroupResponse.json();

      const customFonts = new Map<string, string[]>();
      const customGroup = customGroupData.presentations;
      for (const group of customGroup) {
        const groupName = `custom-${group.presentation_id}`;
        fullDataByGroup.set(groupName, []);
        if (!layoutsByGroup.has(groupName)) {
          layoutsByGroup.set(groupName, new Set());
        }
        const presentationId = group.presentation_id;
        const customLayoutResponse = await fetch(
          `/api/v1/ppt/template-management/get-templates/${presentationId}`
        );
        const customLayoutsData = await customLayoutResponse.json();
        const allLayout = customLayoutsData.layouts;




        const settings = {
          description: `Custom presentation layouts`,
          ordered: false,
          default: false,
        };

        groupSettingsMap.set(`custom-${presentationId}`, settings);
        const groupLayouts: LayoutInfo[] = [];
        const groupFullData: FullDataInfo[] = [];

        // Helper to create an inline error component for this specific slide
        const createErrorComponent = (title: string, message: string): React.ComponentType<{ data: any }> => {
          const ErrorSlide: React.FC<{ data: any }> = () => (
            <div className="aspect-video w-full h-full bg-red-50 text-red-700 flex flex-col items-start justify-start p-4 space-y-2">
              <div className="text-sm font-semibold">{title}</div>
              <pre className="text-xs whitespace-pre-wrap break-words max-h-full overflow-auto bg-red-100 rounded-md p-2 border border-red-200">{message}</pre>
            </div>
          );
          ErrorSlide.displayName = "CustomTemplateErrorSlide";
          return ErrorSlide;
        };

        for (const i of allLayout) {
          try {
            /* ---------- 1. compile JSX to plain script ------------------ */
            const module = compileCustomLayout(i.layout_code, React, z);

            // Determine identifiers even if subsequent steps fail
            const originalLayoutId =
              (module && (module as any).layoutId) ||
              i.layout_name.toLowerCase().replace(/layout$/, "");
            const uniqueKey = `${`custom-${presentationId}`}:${originalLayoutId}`;
            const layoutName =
              (module && (module as any).layoutName) ||
              i.layout_name.replace(/([A-Z])/g, " $1").trim();
            const layoutDescription =
              (module && (module as any).layoutDescription) ||
              `${layoutName} layout for presentations`;

            let fullData: FullDataInfo | null = null;
            let jsonSchema: any = null;
            let componentToUse: React.ComponentType<{ data: any } | any> | null = null;
            let sampleData: any = {};

            // Validate exports
            if (!module || !(module as any).default) {
              const errorComp = createErrorComponent(
                `Invalid export in ${i.layout_name}`,
                "Default export not found. Please export a default React component."
              );
              componentToUse = errorComp;
              jsonSchema = {};
            } else if (!(module as any).Schema) {
              const errorComp = createErrorComponent(
                `Schema missing in ${i.layout_name}`,
                "Schema export not found. Please export a Zod Schema as 'Schema'."
              );
              componentToUse = errorComp;
              jsonSchema = {};
            } else {
              // Cache valid component
              const cacheKey = createCacheKey(
                `custom-${presentationId}`,
                i.layout_name
              );
              if (!layoutCache.has(cacheKey)) {
                layoutCache.set(cacheKey, (module as any).default);
              }
              componentToUse = (module as any).default;

              // Build schema and sample data with guards
              try {
                jsonSchema = z.toJSONSchema((module as any).Schema, {
                  override: (ctx) => {
                    delete ctx.jsonSchema.default;
                  },
                });
              } catch (schemaErr: any) {
                const errorComp = createErrorComponent(
                  `Schema generation failed for ${i.layout_name}`,
                  schemaErr?.message || String(schemaErr)
                );
                componentToUse = errorComp;
                jsonSchema = {};
              }

              if (componentToUse !== null && componentToUse !== (module as any).default) {
                // componentToUse already replaced with error component
                sampleData = {};
              } else {
                try {
                  sampleData = (module as any).Schema.parse({});
                } catch (parseErr: any) {
                  const errorComp = createErrorComponent(
                    `Schema.parse failed for ${i.layout_name}`,
                    parseErr?.message || String(parseErr)
                  );
                  componentToUse = errorComp;
                  sampleData = {};
                  jsonSchema = jsonSchema || {};
                }
              }
            }

            customFonts.set(presentationId, i.fonts);

            const layout: LayoutInfo = {
              id: uniqueKey,
              name: layoutName,
              description: layoutDescription,
              json_schema: jsonSchema,
              groupName: groupName,
            };

            fullData = {
              name: layoutName,
              component: componentToUse as React.ComponentType<any>,
              schema: jsonSchema,
              sampleData: sampleData,
              fileName: i.layout_name,
              groupName: groupName,
              layoutId: uniqueKey,
            };

            groupFullData.push(fullData);

            layoutsById.set(uniqueKey, layout);
            layoutsByGroup.get(groupName)!.add(uniqueKey);
            fileMap.set(uniqueKey, {
              fileName: i.layout_name,
              groupName: groupName,
            });
            groupLayouts.push(layout);
            layouts.push(layout);
          } catch (e: any) {
            // Handle compilation/runtime errors during transformation
            const uniqueKey = `${`custom-${presentationId}`}:${i.layout_name.toLowerCase().replace(/layout$/, "")}`;
            const layoutName = i.layout_name.replace(/([A-Z])/g, " $1").trim();
            const errorComp = createErrorComponent(
              `Compilation error in ${i.layout_name}`,
              e?.message || String(e)
            );

            const layout: LayoutInfo = {
              id: uniqueKey,
              name: layoutName,
              description: `Failed to compile ${i.layout_name}`,
              json_schema: {},
              groupName: groupName,
            };

            const fullData: FullDataInfo = {
              name: layoutName,
              component: errorComp,
              schema: {},
              sampleData: {},
              fileName: i.layout_name,
              groupName: groupName,
              layoutId: uniqueKey,
            };

            groupFullData.push(fullData);
            layoutsById.set(uniqueKey, layout);
            layoutsByGroup.get(groupName)!.add(uniqueKey);
            fileMap.set(uniqueKey, {
              fileName: i.layout_name,
              groupName: groupName,
            });
            groupLayouts.push(layout);
            layouts.push(layout);
          }
        }
        setCustomTemplateFonts(customFonts);
        // Cache grouped layouts
        groupedLayouts.set(groupName, groupLayouts);
        fullDataByGroup.set(groupName, groupFullData);
      }
    } catch (err: any) {
      console.error("Compilation error:", err);
    }


    return {
      layoutsById,
      layoutsByGroup,
      groupSettings: groupSettingsMap,
      fileMap,
      groupedLayouts,
      layoutSchema: layouts,
      fullDataByGroup,
    };
  };

  const getLayout = (
    layoutId: string
  ): React.ComponentType<{ data: any }> | null => {
    if (!layoutData) return null;

    let fileInfo: { fileName: string; groupName: string } | undefined;

    // Search through all fileMap entries to find the layout
    for (const [key, info] of Array.from(layoutData.fileMap.entries())) {
      if (key === layoutId) {
        fileInfo = info;
        break;
      }
    }

    if (!fileInfo) {
      console.warn(`No file info found for layout: ${layoutId}`);
      return null;
    }

    const cacheKey = createCacheKey(fileInfo.groupName, fileInfo.fileName);

    // Return cached layout if available
    if (layoutCache.has(cacheKey)) {
      return layoutCache.get(cacheKey)!;
    }
    // Create and cache layout if not available
    const file = fileInfo.fileName.replace(".tsx", "").replace(".ts", "");
    const Layout = dynamic(
      () => import(`@/presentation-templates/${fileInfo.groupName}/${file}`),
      {
        loading: () => (
          <div className="w-full aspect-[16/9] bg-gray-100 animate-pulse rounded-lg" />
        ),
        ssr: false,
      }
    ) as React.ComponentType<{ data: any }>;

    layoutCache.set(cacheKey, Layout);
    return Layout;
  };

  // Updated accessor methods to handle group-specific lookups
  const getLayoutById = (layoutId: string): LayoutInfo | null => {
    if (!layoutData) return null;

    // Search through all entries to find the layout (since we don't know the group)
    for (const [key, layout] of Array.from(layoutData.layoutsById.entries())) {
      if (key === layoutId) {
        return layout;
      }
    }
    return null;
  };

  const getLayoutByIdAndGroup = (
    layoutId: string,
    groupName: string
  ): LayoutInfo | null => {
    if (!layoutData) return null;
    return layoutData.layoutsById.get(layoutId) || null;
  };

  const getLayoutsByGroup = (groupName: string): LayoutInfo[] => {
    return layoutData?.groupedLayouts.get(groupName) || [];
  };

  const getGroupSetting = (groupName: string): GroupSetting | null => {
    return layoutData?.groupSettings.get(groupName) || null;
  };

  const getAllGroups = (): string[] => {
    return layoutData ? Array.from(layoutData.groupSettings.keys()) : [];
  };

  const getAllLayouts = (): LayoutInfo[] => {
    return layoutData?.layoutSchema || [];
  };

  const getFullDataByGroup = (groupName: string): FullDataInfo[] => {
    return layoutData?.fullDataByGroup.get(groupName) || [];
  };
  const getCustomTemplateFonts = (presentationId: string): string[] | null => {
    return customTemplateFonts.get(presentationId) || null;
  };

  // Load layouts on mount
  useEffect(() => {
    loadLayouts();
  }, []); // Add presentationId to dependency array

  const contextValue: LayoutContextType = {
    getLayoutById,
    getLayoutByIdAndGroup,
    getLayoutsByGroup,
    getGroupSetting,
    getAllGroups,
    getAllLayouts,
    getFullDataByGroup,
    getCustomTemplateFonts,
    loading,
    error,
    getLayout,
    isPreloading,
    cacheSize: layoutCache.size,
    refetch: loadLayouts,
  };

  return (
    <LayoutContext.Provider value={contextValue}>
      {children}
    </LayoutContext.Provider>
  );
};

export const useLayout = (): LayoutContextType => {
  const context = useContext(LayoutContext);
  if (context === undefined) {
    throw new Error("useLayout must be used within a LayoutProvider");
  }
  return context;
};
