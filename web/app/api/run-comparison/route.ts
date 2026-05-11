import { NextRequest, NextResponse } from "next/server";
import { buildRunFileComparison, validateRootFolder } from "@/lib/loadRunArtifacts";
import { DEFAULT_DEMO_ROOT } from "@/lib/defaults";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const rootFolder = searchParams.get("root") || DEFAULT_DEMO_ROOT;
  const leftIteration = parseInt(searchParams.get("leftIteration") || "", 10);
  const rightIteration = parseInt(searchParams.get("rightIteration") || "", 10);
  const leftFilePath = searchParams.get("leftFile");
  const rightFilePath = searchParams.get("rightFile");

  if (Number.isNaN(leftIteration) || Number.isNaN(rightIteration)) {
    return NextResponse.json(
      { error: "Invalid run selection" },
      { status: 400 }
    );
  }

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
    const comparison = await buildRunFileComparison(
      rootFolder,
      leftIteration,
      rightIteration,
      leftFilePath,
      rightFilePath
    );

    return NextResponse.json(comparison);
  } catch (error) {
    console.error("Error loading run comparison:", error);
    return NextResponse.json(
      { error: "Failed to load run comparison" },
      { status: 500 }
    );
  }
}
