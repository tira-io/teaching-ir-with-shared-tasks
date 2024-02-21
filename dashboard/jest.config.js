module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx|jsx)?$': 'ts-jest',
    "^.+\\.(js|jsx)$": "babel-jest",
  },
  "coverageReporters": ["json-summary", "text", "lcov"],
  "collectCoverageFrom" : ["src/ir_datasets.ts", "src/utils.ts", "src/main.ts"],
};
