import { NextRequest, NextResponse } from "next/server";
import { buildRunList, buildChartData } from "@/lib/loadResults";
import { validateRootFolder } from "@/lib/loadRunArtifacts";
import { DEFAULT_DEMO_ROOT } from "@/lib/defaults";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const rootFolder = searchParams.get("root") || DEFAULT_DEMO_ROOT;
  const includeChart = searchParams.get("chart") === "true";

  // Validate the root folder
  const validation = await validateRootFolder(rootFolder);
  if (!validation.valid) {
    return NextResponse.json(
      {
        error: "Invalid root folder",
        details: validation.errors,
      },
      { status: 400 }
    );
  }

  try {
    const runs = await buildRunList(rootFolder);
    
    if (includeChart) {
      const chartData = await buildChartData(rootFolder);
      return NextResponse.json({ runs, chartData });
    }
    
    return NextResponse.json({ runs });
  } catch (error) {
    console.error("Error loading runs:", error);
    return NextResponse.json(
      { error: "Failed to load runs" },
      { status: 500 }
    );
  }
}
