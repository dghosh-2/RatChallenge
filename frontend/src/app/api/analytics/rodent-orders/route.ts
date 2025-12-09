import { NextResponse } from 'next/server';
import analyticsData from '../../../../../public/analytics-data.json';

export async function GET() {
  return NextResponse.json(analyticsData.rodent_orders);
}

