import { NextRequest, NextResponse } from "next/server";
import { buildProjectSummary } from "@/lib/loadResults";
import { validateRootFolder } from "@/lib/loadRunArtifacts";
import { DEFAULT_DEMO_ROOT } from "@/lib/defaults";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const rootFolder = searchParams.get("root") || DEFAULT_DEMO_ROOT;

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
    const summary = await buildProjectSummary(rootFolder);
    return NextResponse.json(summary);
  } catch (error) {
    console.error("Error building project summary:", error);
    return NextResponse.json(
      { error: "Failed to load project summary" },
      { status: 500 }
    );
  }
}
