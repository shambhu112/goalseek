type YamlScalar = string | number | boolean | null;
type YamlValue = YamlScalar | YamlObject | YamlValue[];
type YamlObject = Record<string, YamlValue>;

interface StackEntry {
  indent: number;
  value: YamlObject | YamlValue[];
}

function findNextMeaningfulLineIndex(lines: string[], startIndex: number): number {
  for (let i = startIndex; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (trimmed && !trimmed.startsWith("#")) {
      return i;
    }
  }

  return -1;
}

function parseScalar(rawValue: string): YamlScalar {
  const value = rawValue.trim();

  if (!value) {
    return "";
  }

  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }

  if (value === "null") return null;
  if (value === "true") return true;
  if (value === "false") return false;
  if (/^-?\d+(?:\.\d+)?$/.test(value)) return Number(value);

  return value;
}

function getChildContainerType(lines: string[], parentIndex: number): "array" | "object" {
  const nextIndex = findNextMeaningfulLineIndex(lines, parentIndex + 1);
  if (nextIndex === -1) {
    return "object";
  }

  const nextLine = lines[nextIndex];
  const nextIndent = nextLine.match(/^ */)?.[0].length ?? 0;
  const parentIndent = lines[parentIndex].match(/^ */)?.[0].length ?? 0;

  if (nextIndent <= parentIndent) {
    return "object";
  }

  return nextLine.trim().startsWith("- ") ? "array" : "object";
}

function parseListItem(
  itemContent: string,
  lines: string[],
  lineIndex: number
): YamlValue {
  if (!itemContent) {
    return {};
  }

  const mappingMatch = itemContent.match(/^([^:]+):\s*(.*)$/);
  if (!mappingMatch) {
    return parseScalar(itemContent);
  }

  const [, rawKey, rawValue] = mappingMatch;
  const key = rawKey.trim();
  const value = rawValue.trim();
  const obj: YamlObject = {};

  if (value) {
    obj[key] = parseScalar(value);
    return obj;
  }

  obj[key] = getChildContainerType(lines, lineIndex) === "array" ? [] : {};
  return obj;
}

export function parseSimpleYaml(content: string): YamlObject {
  const root: YamlObject = {};
  const lines = content.split(/\r?\n/);
  const stack: StackEntry[] = [{ indent: -1, value: root }];

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
    const line = lines[lineIndex];
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const indent = line.match(/^ */)?.[0].length ?? 0;

    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) {
      stack.pop();
    }

    const parent = stack[stack.length - 1]?.value;
    if (!parent) {
      continue;
    }

    if (trimmed.startsWith("- ")) {
      if (!Array.isArray(parent)) {
        continue;
      }

      const item = parseListItem(trimmed.slice(2).trim(), lines, lineIndex);
      parent.push(item);

      if (item && typeof item === "object") {
        stack.push({ indent, value: item as YamlObject | YamlValue[] });
      }

      continue;
    }

    const separatorIndex = trimmed.indexOf(":");
    if (separatorIndex === -1 || Array.isArray(parent)) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    const rawValue = trimmed.slice(separatorIndex + 1).trim();

    if (rawValue) {
      parent[key] = parseScalar(rawValue);
      continue;
    }

    const child = getChildContainerType(lines, lineIndex) === "array" ? [] : {};
    parent[key] = child;
    stack.push({ indent, value: child });
  }

  return root;
}
