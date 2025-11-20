import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import Anthropic from '@anthropic-ai/sdk';
import { ANTHROPIC_API_KEY } from '$env/static/private';
import type { FullInstructorInformation } from '$lib/types/instructor';
import { calculateGradePointAverage, calculateARate } from '$lib/types/madgrades';

export const POST: RequestHandler = async ({ request }) => {
	if (!ANTHROPIC_API_KEY) {
		throw error(500, 'Anthropic API key not configured');
	}

	const instructor: FullInstructorInformation = await request.json();

	// Build context from available instructor data
	const contextParts: string[] = [];

	// Basic info
	if (instructor.position) {
		contextParts.push(`Position: ${instructor.position}`);
	}
	if (instructor.department) {
		contextParts.push(`Department: ${instructor.department}`);
	}
	if (instructor.credentials) {
		contextParts.push(`Credentials: ${instructor.credentials}`);
	}

	// Grade statistics
	if (instructor.cumulative_grade_data) {
		const avgGpa = calculateGradePointAverage(instructor.cumulative_grade_data);
		if (avgGpa) {
			contextParts.push(`Average GPA: ${avgGpa.toFixed(2)}`);
		}

		const total = instructor.cumulative_grade_data.total;
		if (total) {
			contextParts.push(`Total students taught: ${total}`);
		}

		const aRate = calculateARate(instructor.cumulative_grade_data);
		if (aRate) {
			contextParts.push(`A/AB rate: ${aRate.toFixed(1)}%`);
		}
	}

	// RateMyProfessors data
	if (instructor.rmp_data) {
		const rmp = instructor.rmp_data;
		contextParts.push(
			`RateMyProfessors rating: ${rmp.average_rating.toFixed(1)}/5.0 (${rmp.num_ratings} ratings)`
		);
		contextParts.push(`Difficulty rating: ${rmp.average_difficulty.toFixed(1)}/5.0`);
		if (rmp.would_take_again_percent > 0) {
			contextParts.push(`Would take again: ${rmp.would_take_again_percent}%`);
		}

		// Sample a few student comments for context
		if (rmp.ratings && rmp.ratings.length > 0) {
			const sampleSize = Math.min(5, rmp.ratings.length);
			const sampleComments = rmp.ratings
				.slice(0, sampleSize)
				.map((r) => r.comment)
				.filter((c) => c);

			if (sampleComments.length > 0) {
				contextParts.push(`\nSample student reviews:\n${sampleComments.map((c) => `- ${c}`).join('\n')}`);
			}
		}
	}

	// Courses taught
	if (instructor.courses_taught) {
		const courseCount = instructor.courses_taught.length;
		contextParts.push(`Number of different courses taught: ${courseCount}`);
	}

	if (contextParts.length === 0) {
		throw error(400, 'Insufficient instructor data to generate summary');
	}

	const context = contextParts.join('\n');

	// Generate summary using Anthropic API
	try {
		const client = new Anthropic({ apiKey: ANTHROPIC_API_KEY });

		const prompt = `Based on the following information about ${instructor.name}, a faculty member at the University of Wisconsin-Madison, write a concise 2-3 sentence professional summary that would be helpful for students considering taking their courses.

Instructor Data:
${context}

Focus on their teaching style, student feedback patterns, and what makes them distinctive as an instructor. Be objective and balanced. Do not make up information not provided in the data.`;

		const message = await client.messages.create({
			model: 'claude-3-5-haiku-20241022',
			max_tokens: 300,
			messages: [{ role: 'user', content: prompt }]
		});

		const summary = message.content[0].type === 'text' ? message.content[0].text.trim() : '';

		return json({ summary });
	} catch (err) {
		console.error('Failed to generate instructor summary:', err);
		throw error(500, 'Failed to generate summary');
	}
};
