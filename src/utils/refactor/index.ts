const libPath = `${__dirname}/../../../lib/refactor`

const jsCommand = ['node', `${libPath}/javascript/main.js`]
const pyCommand = ['python3', `${libPath}/python/main.py`]
const javaCommand = ['java', `${libPath}/java/JavaEngine.class`]

export const ENGINES: Record<string, string[][]> = {
    js: [jsCommand],
    jsx: [jsCommand],
    ts: [jsCommand],
    tsx: [jsCommand],
    py: [pyCommand],
    java: [javaCommand]
}