/**
 * Jest Configuration for Frontend Tests
 * React component testing with Testing Library
 */

module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src', '<rootDir>/tests/frontend'],
  setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.ts'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/tests/frontend/__mocks__/fileMock.js',
  },
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/tests/',
    '\\.stories\\.',
  ],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  testMatch: [
    '**/__tests__/**/*.(test|spec).(ts|tsx)',
    '**/tests/frontend/**/*.(test|spec).(ts|tsx)',
  ],
  globals: {
    'ts-jest': {
      tsconfig: {
        jsx: 'react',
        esModuleInterop: true,
      },
    },
  },
};
