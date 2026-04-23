import { NextRequest, NextResponse } from "next/server";
import { buildRunViewModel, validateRootFolder } from "@/lib/loadRunArtifacts";
import { DEFAULT_DEMO_ROOT } from "@/lib/defaults";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ iteration: string }> }
) {
  const { iteration: iterationParam } = await params;
  const searchParams = request.nextUrl.searchParams;
  const rootFolder = searchParams.get("root") || DEFAULT_DEMO_ROOT;

  const iteration = parseInt(iterationParam, 10);
  if (isNaN(iteration)) {
    return NextResponse.json(
      { error: "Invalid iteration number" },
      { status: 400 }
    );
  }

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
    const run = await buildRunViewModel(rootFolder, iteration);

    if (!run) {
      return NextResponse.json(
        { error: `Run with iteration ${iteration} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json(run);
  } catch (error) {
    console.error(`Error loading run ${iteration}:`, error);
    return NextResponse.json(
      { error: "Failed to load run details" },
      { status: 500 }
    );
  }
}
