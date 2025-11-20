import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import Anthropic from '@anthropic-ai/sdk';
import { env } from '$env/dynamic/private';

export const POST: RequestHandler = async ({ request }) => {
	try {
		const { courseTitle, courseDescription, courseNumber, subject, instructors } = await request.json();

		if (!courseTitle || !courseDescription) {
			throw error(400, 'Missing required fields: courseTitle and courseDescription');
		}

		if (!env.ANTHROPIC_API_KEY || env.ANTHROPIC_API_KEY === 'CHANGEME') {
			throw error(500, 'ANTHROPIC_API_KEY is not configured');
		}

		const anthropic = new Anthropic({
			apiKey: env.ANTHROPIC_API_KEY
		});

		// Format instructor information for the prompt
		let instructorInfo = '';
		if (instructors && instructors.length > 0) {
			instructorInfo = '\n\nInstructor Statistics:\n';
			instructors.forEach((instructor: any) => {
				instructorInfo += `- ${instructor.name}: ${instructor.rating?.toFixed(1)}/5.0 rating`;
				if (instructor.wouldTakeAgain) {
					instructorInfo += `, ${instructor.wouldTakeAgain}% would take again`;
				}
				if (instructor.difficulty) {
					instructorInfo += `, ${instructor.difficulty.toFixed(1)}/5.0 difficulty`;
				}
				if (instructor.numRatings) {
					instructorInfo += ` (${instructor.numRatings} ratings)`;
				}
				instructorInfo += '\n';
			});
		}

		const stream = await anthropic.messages.stream({
			model: 'claude-haiku-4-5-20251001',
			max_tokens: 1024,
			messages: [
				{
					role: 'user',
					content: `Please provide a concise, engaging summary (2-3 sentences) of this University of Wisconsin-Madison course that would help students decide if they want to take it. Focus on what students will learn and why it matters. If instructor ratings are provided, briefly mention instructor quality.

Course: ${subject ? subject + ' ' : ''}${courseNumber || ''} - ${courseTitle}
Description: ${courseDescription}${instructorInfo}

Provide only the summary, without any preamble or additional formatting.`
				}
			]
		});

		const encoder = new TextEncoder();
		const readableStream = new ReadableStream({
			async start(controller) {
				try {
					for await (const chunk of stream) {
						if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
							const text = chunk.delta.text;
							controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
						}
					}
					controller.enqueue(encoder.encode('data: [DONE]\n\n'));
					controller.close();
				} catch (err) {
					console.error('Streaming error:', err);
					controller.error(err);
				}
			}
		});

		return new Response(readableStream, {
			headers: {
				'Content-Type': 'text/event-stream',
				'Cache-Control': 'no-cache',
				'Connection': 'keep-alive'
			}
		});
	} catch (err) {
		console.error('Error generating summary:', err);
		if (err instanceof Error) {
			throw error(500, `Failed to generate summary: ${err.message}`);
		}
		throw error(500, 'Failed to generate summary');
	}
};
