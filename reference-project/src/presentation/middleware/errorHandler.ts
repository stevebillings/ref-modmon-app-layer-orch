import { Request, Response, NextFunction } from 'express';

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

  res.status(400).json({
    success: false,
    error: error.message,
    ...(isDevelopment && { stack: error.stack }),
  });
}
