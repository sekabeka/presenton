import { CheckCircle } from "lucide-react";
import React from "react";
import { usePathname } from "next/navigation";
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";
import { Template } from "../types/index";
import { useLayout } from "../../context/LayoutContext";
import { useFontLoader } from "../../hooks/useFontLoader";
interface TemplateLayoutsProps {
  template: Template;
  onSelectTemplate: (template: Template) => void;
  selectedTemplate: Template | null;
}

const TemplateLayouts: React.FC<TemplateLayoutsProps> = ({
  template,
  onSelectTemplate,
  selectedTemplate,
}) => {
  const { getFullDataByTemplateID, getCustomTemplateFonts } = useLayout();
  const layoutTemplate = getFullDataByTemplateID(template.id);
  const fonts = getCustomTemplateFonts(template.id.split("custom-")[1]);
  useFontLoader(fonts || []);
  const pathname = usePathname();
  return (
    <div
      onClick={() => {
        trackEvent(MixpanelEvent.Group_Layout_Selected_Clicked, { pathname });
        onSelectTemplate(template);
      }}
      className={`relative p-4 rounded-lg border cursor-pointer transition-all duration-200 ${selectedTemplate?.id === template.id
        ? "border-blue-500 bg-blue-50 shadow-md"
        : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
        }`}
    >
      {selectedTemplate?.id === template.id && (
        <div className="absolute top-3 right-3">
          <CheckCircle className="w-5 h-5 text-blue-500" />
        </div>
      )}

      <div className="mb-3 ">
        <h6 className="text-base capitalize font-medium text-gray-900 mb-1">
          {template.name}
        </h6>
        <p className="text-sm text-gray-600">{template.description}</p>
      </div>

      {/* Layout previews */}
      <div className="grid grid-cols-2 gap-2 mb-3 min-h-[300px]">
        {layoutTemplate &&
          layoutTemplate?.slice(0, 4).map((layout: any, index: number) => {
            const {
              component: LayoutComponent,
              sampleData,
              layoutId,
              templateID,
            } = layout;
            return (
              <div
                key={`${templateID}-${index}`}
                className=" relative cursor-pointer overflow-hidden aspect-video"
              >
                <div className="absolute cursor-pointer bg-transparent z-40 top-0 left-0 w-full h-full" />
                <div className="transform scale-[0.2] flex justify-center items-center origin-top-left  w-[500%] h-[500%]">
                  <LayoutComponent data={sampleData} />
                </div>
              </div>
            );
          })}
      </div>

      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{layoutTemplate?.length} layouts</span>
        <span
          className={`px-2 py-1 rounded text-xs ${template.ordered
            ? "bg-gray-100 text-gray-700"
            : "bg-blue-100 text-blue-700"
            }`}
        >
          {template.ordered ? "Structured" : "Flexible"}
        </span>
      </div>
    </div>
  );
};

export default TemplateLayouts;
