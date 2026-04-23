import { NextRequest, NextResponse } from "next/server";
import { validateRootFolder } from "@/lib/loadRunArtifacts";

export async function POST(request: NextRequest) {
  try {
    const { rootFolder } = await request.json();

    if (!rootFolder || typeof rootFolder !== "string") {
      return NextResponse.json(
        { error: "rootFolder is required and must be a string" },
        { status: 400 }
      );
    }

    const validation = await validateRootFolder(rootFolder);
    return NextResponse.json(validation);
  } catch (error) {
    console.error("Error validating root folder:", error);
    return NextResponse.json(
      { error: "Failed to validate root folder" },
      { status: 500 }
    );
  }
}
