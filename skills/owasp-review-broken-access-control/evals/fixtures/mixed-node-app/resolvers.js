const { Invoice, Refund } = require('./stores');

module.exports = {
  Query: {
    invoice: (_, { id }) => Invoice.findByPk(id),
  },
  Mutation: {
    approveRefund: async (_, { id }, context) => {
      const refund = await Refund.findByPk(id);
      refund.status = 'approved';
      refund.approvedBy = context.user.id;
      return refund.save();
    },
  },
};
