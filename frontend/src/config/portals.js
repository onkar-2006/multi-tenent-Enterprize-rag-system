// Configuration file for the 4 Enterprise Client Portals & Pre-Signed Test Tokens

export const API_BASE_URL = 'http://127.0.0.1:8000';

export const PORTALS = {
  hr: {
    id: 'hr',
    name: 'HR Self-Service Portal',
    company: 'ApexTech Enterprise HR',
    scope: 'hr',
    role: 'employee',
    colorTheme: 'hr',
    iconName: 'Users',
    description: 'Access company PTO policies, benefits guidelines, HR leave requests, and employee compliance documents.',
    suggestedPrompts: [
      'What is the paid time off (PTO) policy?',
      'How many annual leave days do employees get?',
      'Request PTO for next Monday',
      'What health insurance plans are offered?'
    ]
  },
  it: {
    id: 'it',
    name: 'IT Helpdesk Portal',
    company: 'ApexTech IT Operations',
    scope: 'it',
    role: 'employee',
    colorTheme: 'it',
    iconName: 'Laptop',
    description: 'Hardware replacement procedures, VPN troubleshooting, software licenses, and IT security protocols.',
    suggestedPrompts: [
      'What is the laptop replacement policy?',
      'How do I request a password reset?',
      'How do I set up the corporate VPN?',
      'What is the policy for software installation?'
    ]
  },
  support: {
    id: 'support',
    name: 'Customer Support Desk',
    company: 'ApexTech Global Support',
    scope: 'customer_support',
    role: 'agent',
    colorTheme: 'support',
    iconName: 'Headphones',
    description: 'Customer SLA commitments, ticketing escalation matrix, return policies, and product support knowledgebase.',
    suggestedPrompts: [
      'What are our standard SLA response times?',
      'How do I escalate an urgent customer ticket?',
      'What is the customer product refund policy?',
      'How to resolve API connection timeouts?'
    ]
  },
  sales: {
    id: 'sales',
    name: 'Sales Intelligence Portal',
    company: 'ApexTech Commercial Sales',
    scope: 'sales',
    role: 'sales_rep',
    colorTheme: 'sales',
    iconName: 'TrendingUp',
    description: 'Enterprise pricing tiers, competitor comparison matrix, discount authorization limits, and product pitch sheets.',
    suggestedPrompts: [
      'What are the enterprise software pricing tiers?',
      'What is the maximum discount a sales rep can offer?',
      'How do we compare against main competitors?',
      'Request discount approval for a 500-seat deal'
    ]
  }
};
