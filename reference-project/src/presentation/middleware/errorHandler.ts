import { Request, Response, NextFunction } from 'express';

/**
 * Custom error classes for better error handling
 */
export class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Error handling middleware
 * 
 * Catches errors from controllers and formats error responses.
 */
export function errorHandler(
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  console.error('Error:', error);

  // In production, don't expose internal error details
  const isDevelopment = process.env.NODE_ENV !== 'production';

  // Determine status code based on error type
  let statusCode = 400; // Default to Bad Request
  
  if (error instanceof NotFoundError) {
    statusCode = 404;
  } else if (error instanceof ValidationError) {
    statusCode = 422; // Unprocessable Entity
  } else if (error.name === 'ValidationError') {
    statusCode = 422;
  }

  res.status(statusCode).json({
    success: false,
    error: error.message,
    ...(isDevelopment && { stack: error.stack }),
  });
}
